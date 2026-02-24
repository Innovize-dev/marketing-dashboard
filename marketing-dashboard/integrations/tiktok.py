"""
TikTok for Business Ads API adapter.

Required credentials:
  access_token   - OAuth 2.0 access token
  advertiser_id  - TikTok Ads advertiser ID

No official Python SDK — uses TikTok Marketing API v1.3 REST directly.
Base URL: https://business-api.tiktok.com/open_api/v1.3/

Interactions = video_play_actions (plays as "interactions" for video-first platform).
Revenue      = real_time_conversion_value (if conversion tracking is set up).
"""
from __future__ import annotations

import json
from typing import Optional

import requests

from integrations.base import DateRange, PlatformAdapter, RawCampaignRow

_BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"


class TikTokAdapter(PlatformAdapter):
    def __init__(self, creds: dict):
        self.advertiser_id = creds["advertiser_id"]
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Access-Token": creds["access_token"],
                "Content-Type": "application/json",
            }
        )

    def _get(self, endpoint: str, params: dict) -> dict:
        response = self._session.get(f"{_BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise ValueError(
                f"TikTok API error {data.get('code')}: {data.get('message')}"
            )
        return data["data"]

    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        # TikTok always returns daily rows; resample in transformer
        params = {
            "advertiser_id": self.advertiser_id,
            "report_type": "CAMPAIGN",
            "dimensions": json.dumps(["campaign_id", "stat_time_day"]),
            "metrics": json.dumps(
                [
                    "campaign_name",
                    "impressions",
                    "clicks",
                    "conversion",
                    "spend",
                    "real_time_conversion_value",
                    "video_play_actions",
                ]
            ),
            "start_date": str(date_range.start),
            "end_date": str(date_range.end),
            "page_size": 1000,
        }
        data = self._get("/report/integrated/get/", params)
        rows = []
        for item in data.get("list", []):
            dims = item["dimensions"]
            metrics = item["metrics"]
            cid = dims.get("campaign_id", "")
            if campaign_ids and cid not in campaign_ids:
                continue
            period_raw = dims.get("stat_time_day", "")
            period = period_raw[:10] if period_raw else ""
            rows.append(
                RawCampaignRow(
                    platform="tiktok",
                    period=period,
                    campaign_id=cid,
                    campaign_name=metrics.get("campaign_name", ""),
                    impressions=int(metrics.get("impressions", 0) or 0),
                    clicks=int(metrics.get("clicks", 0) or 0),
                    interactions=int(metrics.get("video_play_actions", 0) or 0),
                    conversions=float(metrics.get("conversion", 0) or 0),
                    spend=float(metrics.get("spend", 0) or 0),
                    revenue=float(
                        metrics.get("real_time_conversion_value", 0) or 0
                    ),
                )
            )
        return rows

    def list_campaigns(self) -> list[dict]:
        params = {
            "advertiser_id": self.advertiser_id,
            "fields": json.dumps(["campaign_id", "campaign_name", "operation_status"]),
            "page_size": 1000,
        }
        data = self._get("/campaign/get/", params)
        return [
            {
                "id": c["campaign_id"],
                "name": c["campaign_name"],
                "status": c.get("operation_status", ""),
            }
            for c in data.get("list", [])
        ]

    def validate_credentials(self) -> bool:
        try:
            params = {
                "advertiser_ids": json.dumps([self.advertiser_id]),
                "fields": json.dumps(["advertiser_id"]),
            }
            self._get("/advertiser/info/", params)
            return True
        except Exception:
            return False
