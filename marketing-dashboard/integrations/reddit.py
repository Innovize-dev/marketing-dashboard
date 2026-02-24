"""
Reddit Ads API adapter.

Required credentials:
  client_id      - Reddit app client ID
  client_secret  - Reddit app client secret
  access_token   - OAuth2 bearer token
  account_id     - Reddit Ads account ID (t2_XXXXXXXX format)

Uses Reddit Ads API v3 REST.
Spend is returned in cents; converted to USD here.
Interactions = clicks (Reddit has no separate engagement metric).
"""
from __future__ import annotations

from typing import Optional

import requests

from integrations.base import DateRange, PlatformAdapter, RawCampaignRow

_BASE_URL = "https://ads-api.reddit.com/api/v3"


class RedditAdapter(PlatformAdapter):
    def __init__(self, creds: dict):
        self.account_id = creds["account_id"]
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {creds['access_token']}",
                "User-Agent": "MarketingDashboard/1.0",
            }
        )

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        response = self._session.get(
            f"{_BASE_URL}{endpoint}", params=params or {}
        )
        response.raise_for_status()
        return response.json()

    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        granularity_map = {"daily": "DAY", "weekly": "WEEK", "monthly": "MONTH"}
        params = {
            "entity": "CAMPAIGN",
            "fields": "impressions,clicks,spend,conversion_value_d,conversions_d",
            "start_time": str(date_range.start),
            "end_time": str(date_range.end),
            "interval": granularity_map.get(granularity, "DAY"),
        }
        data = self._get(f"/accounts/{self.account_id}/reports", params)
        rows = []
        for item in data.get("data", []):
            cid = item.get("id", "")
            if campaign_ids and cid not in campaign_ids:
                continue
            campaign_name = item.get("name", "")
            for interval in item.get("intervals", []):
                period = (interval.get("start_time") or "")[:10]
                spend_cents = float(interval.get("spend", 0) or 0)
                rows.append(
                    RawCampaignRow(
                        platform="reddit",
                        period=period,
                        campaign_id=cid,
                        campaign_name=campaign_name,
                        impressions=int(interval.get("impressions", 0) or 0),
                        clicks=int(interval.get("clicks", 0) or 0),
                        interactions=int(interval.get("clicks", 0) or 0),
                        conversions=float(
                            interval.get("conversions_d", 0) or 0
                        ),
                        spend=spend_cents / 100,  # cents → USD
                        revenue=float(
                            interval.get("conversion_value_d", 0) or 0
                        ),
                    )
                )
        return rows

    def list_campaigns(self) -> list[dict]:
        data = self._get(f"/accounts/{self.account_id}/campaigns")
        return [
            {
                "id": c.get("id", ""),
                "name": c.get("name", ""),
                "status": c.get("status", ""),
            }
            for c in data.get("data", [])
        ]

    def validate_credentials(self) -> bool:
        try:
            self._get(f"/accounts/{self.account_id}")
            return True
        except Exception:
            return False
