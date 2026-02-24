"""
Google Analytics 4 (GA4) Data API adapter.

Required credentials:
  property_id          - numeric GA4 property ID (e.g. "123456789")
  service_account_json - raw JSON string of a service account key file
                         (or leave blank to use Application Default Credentials)

GA4 reports conversions, sessions (as interactions), and revenue.
Impressions, clicks, and spend are not available from GA4; those fields are
left as 0 — they are populated from Google Ads in the merger step.
"""
from __future__ import annotations

import json
from typing import Optional

from integrations.base import DateRange, PlatformAdapter, RawCampaignRow


class GA4Adapter(PlatformAdapter):
    def __init__(self, creds: dict):
        from google.analytics.data_v1beta import BetaAnalyticsDataClient

        self.property_id = creds["property_id"]
        sa_json = creds.get("service_account_json", "")

        if sa_json:
            from google.oauth2 import service_account

            # Accept either raw JSON string or a file path
            try:
                sa_info = json.loads(sa_json)
            except json.JSONDecodeError:
                with open(sa_json) as f:
                    sa_info = json.load(f)

            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            self.client = BetaAnalyticsDataClient(credentials=credentials)
        else:
            # Application Default Credentials
            self.client = BetaAnalyticsDataClient()

    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        from google.analytics.data_v1beta.types import (
            DateRange as GA4DateRange,
            Dimension,
            Metric,
            RunReportRequest,
        )

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="sessionCampaignName"),
                Dimension(name="sessionCampaignId"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="totalRevenue"),
            ],
            date_ranges=[
                GA4DateRange(
                    start_date=str(date_range.start),
                    end_date=str(date_range.end),
                )
            ],
        )
        response = self.client.run_report(request)
        rows = []
        for row in response.rows:
            dims = row.dimension_values
            vals = row.metric_values
            raw_date = dims[0].value  # YYYYMMDD
            period = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            rows.append(
                RawCampaignRow(
                    platform="ga4",
                    period=period,
                    campaign_name=dims[1].value,
                    campaign_id=dims[2].value,
                    impressions=0,
                    clicks=0,
                    interactions=int(float(vals[0].value)),  # sessions
                    conversions=float(vals[1].value),
                    spend=0.0,
                    revenue=float(vals[2].value),
                )
            )
        return rows

    def list_campaigns(self) -> list[dict]:
        from google.analytics.data_v1beta.types import (
            DateRange as GA4DateRange,
            Dimension,
            Metric,
            RunReportRequest,
        )
        from datetime import date, timedelta

        today = date.today()
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="sessionCampaignName"),
                Dimension(name="sessionCampaignId"),
            ],
            metrics=[Metric(name="sessions")],
            date_ranges=[
                GA4DateRange(
                    start_date=str(today - timedelta(days=90)),
                    end_date=str(today),
                )
            ],
        )
        response = self.client.run_report(request)
        return [
            {
                "id": row.dimension_values[1].value,
                "name": row.dimension_values[0].value,
                "status": "ACTIVE",
            }
            for row in response.rows
        ]

    def validate_credentials(self) -> bool:
        try:
            self.list_campaigns()
            return True
        except Exception:
            return False
