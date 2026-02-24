"""
Meta (Facebook / Instagram) Marketing API adapter.

Required credentials:
  app_id         - Meta App ID
  app_secret     - Meta App Secret
  access_token   - Long-lived User token or System User token
  ad_account_id  - Format: "act_XXXXXXXXXX"

Uses the official facebook-business Python SDK.
Interactions = post_engagement action type.
Conversions   = purchase action type (change to your primary conversion event).
Revenue       = purchase action_values.
"""
from __future__ import annotations

from typing import Optional

from integrations.base import DateRange, PlatformAdapter, RawCampaignRow

# Action types mapped to "conversions" and "revenue" — adjust to match your
# primary conversion event if it is not "purchase".
_CONVERSION_ACTION = "purchase"


class MetaAdapter(PlatformAdapter):
    def __init__(self, creds: dict):
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount

        FacebookAdsApi.init(
            app_id=creds["app_id"],
            app_secret=creds["app_secret"],
            access_token=creds["access_token"],
        )
        self.account = AdAccount(creds["ad_account_id"])

    @staticmethod
    def _extract_action(actions: list, action_type: str) -> float:
        for action in actions or []:
            if action.get("action_type") == action_type:
                return float(action.get("value", 0))
        return 0.0

    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        from facebook_business.adobjects.adsinsights import AdsInsights

        fields = [
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.date_start,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.actions,
            AdsInsights.Field.action_values,
            AdsInsights.Field.spend,
        ]
        params = {
            "level": "campaign",
            "time_increment": 1,  # always fetch daily; resample downstream
            "time_range": {
                "since": str(date_range.start),
                "until": str(date_range.end),
            },
        }
        if campaign_ids:
            params["filtering"] = [
                {"field": "campaign.id", "operator": "IN", "value": campaign_ids}
            ]

        insights = self.account.get_insights(fields=fields, params=params)
        rows = []
        for insight in insights:
            actions = insight.get("actions", [])
            action_values = insight.get("action_values", [])
            rows.append(
                RawCampaignRow(
                    platform="meta",
                    period=insight["date_start"],
                    campaign_id=insight["campaign_id"],
                    campaign_name=insight["campaign_name"],
                    impressions=int(insight.get("impressions", 0)),
                    clicks=int(insight.get("clicks", 0)),
                    interactions=int(
                        self._extract_action(actions, "post_engagement")
                    ),
                    conversions=self._extract_action(actions, _CONVERSION_ACTION),
                    spend=float(insight.get("spend", 0)),
                    revenue=self._extract_action(action_values, _CONVERSION_ACTION),
                )
            )
        return rows

    def list_campaigns(self) -> list[dict]:
        from facebook_business.adobjects.campaign import Campaign

        campaigns = self.account.get_campaigns(
            fields=[
                Campaign.Field.id,
                Campaign.Field.name,
                Campaign.Field.status,
            ]
        )
        return [
            {"id": c["id"], "name": c["name"], "status": c["status"]}
            for c in campaigns
        ]

    def validate_credentials(self) -> bool:
        try:
            self.account.api_get(fields=["id"])
            return True
        except Exception:
            return False
