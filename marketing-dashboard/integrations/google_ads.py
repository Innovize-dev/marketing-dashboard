"""
Google Ads API adapter.

Required credentials:
  developer_token, client_id, client_secret, refresh_token,
  customer_id (10-digit, no dashes), login_customer_id (optional MCC ID)

Uses the google-ads Python library with GAQL queries.
cost_micros is converted to USD by dividing by 1,000,000.
"""
from __future__ import annotations

from typing import Optional

from integrations.base import DateRange, PlatformAdapter, RawCampaignRow


class GoogleAdsAdapter(PlatformAdapter):
    def __init__(self, creds: dict):
        from google.ads.googleads.client import GoogleAdsClient

        config = {
            "developer_token": creds["developer_token"],
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "use_proto_plus": True,
        }
        if creds.get("login_customer_id"):
            config["login_customer_id"] = creds["login_customer_id"]

        self.client = GoogleAdsClient.load_from_dict(config)
        self.customer_id = creds["customer_id"].replace("-", "")
        self._ga_service = None

    @property
    def ga_service(self):
        if self._ga_service is None:
            self._ga_service = self.client.get_service("GoogleAdsService")
        return self._ga_service

    def _build_query(self, date_range: DateRange) -> str:
        return f"""
            SELECT
                campaign.id,
                campaign.name,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.interactions,
                metrics.conversions,
                metrics.cost_micros,
                metrics.all_conversions_value
            FROM campaign
            WHERE
                segments.date BETWEEN '{date_range.start}' AND '{date_range.end}'
                AND campaign.status != 'REMOVED'
            ORDER BY segments.date DESC
        """

    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        query = self._build_query(date_range)
        stream = self.ga_service.search_stream(
            customer_id=self.customer_id, query=query
        )
        rows = []
        for batch in stream:
            for row in batch.results:
                cid = str(row.campaign.id)
                if campaign_ids and cid not in campaign_ids:
                    continue
                rows.append(
                    RawCampaignRow(
                        platform="google_ads",
                        period=str(row.segments.date),
                        campaign_id=cid,
                        campaign_name=row.campaign.name,
                        impressions=row.metrics.impressions,
                        clicks=row.metrics.clicks,
                        interactions=row.metrics.interactions,
                        conversions=row.metrics.conversions,
                        spend=row.metrics.cost_micros / 1_000_000,
                        revenue=row.metrics.all_conversions_value,
                    )
                )
        return rows

    def list_campaigns(self) -> list[dict]:
        query = """
            SELECT campaign.id, campaign.name, campaign.status
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY campaign.name
        """
        response = self.ga_service.search(
            customer_id=self.customer_id, query=query
        )
        return [
            {
                "id": str(r.campaign.id),
                "name": r.campaign.name,
                "status": r.campaign.status.name,
            }
            for r in response
        ]

    def validate_credentials(self) -> bool:
        try:
            query = "SELECT customer.id FROM customer LIMIT 1"
            self.ga_service.search(customer_id=self.customer_id, query=query)
            return True
        except Exception:
            return False
