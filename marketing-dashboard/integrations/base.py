"""
Abstract base class and shared data types for all platform adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DateRange:
    start: date
    end: date

    def __str__(self) -> str:
        return f"{self.start} to {self.end}"


@dataclass
class RawCampaignRow:
    """
    Canonical row returned by every platform adapter before normalization.
    All monetary values are in USD. Dates are ISO-format strings (YYYY-MM-DD).
    """
    platform: str
    period: str                  # YYYY-MM-DD (always daily; resampling happens downstream)
    campaign_id: str
    campaign_name: str
    impressions: int = 0
    clicks: int = 0
    interactions: int = 0        # platform-specific engagement (see adapter docstrings)
    conversions: float = 0.0
    spend: float = 0.0           # USD
    revenue: Optional[float] = None


class PlatformAdapter(ABC):
    """
    Interface every integration must implement.
    Adapters are stateless after __init__ — all state lives in the creds dict
    passed at construction time.
    """

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Performs a lightweight API call to verify credentials are valid.
        Returns True on success, False (or raises) on failure.
        """
        ...

    @abstractmethod
    def fetch_campaigns(
        self,
        date_range: DateRange,
        granularity: str = "daily",
        campaign_ids: Optional[list[str]] = None,
    ) -> list[RawCampaignRow]:
        """
        Returns a flat list of RawCampaignRow for the given date range.
        granularity is a hint — adapters always return daily rows; the pipeline
        resamples to weekly/monthly downstream.
        campaign_ids: optional filter; if None, returns all campaigns.
        """
        ...

    @abstractmethod
    def list_campaigns(self) -> list[dict]:
        """
        Returns a list of campaign dicts: [{"id": str, "name": str, "status": str}]
        Used to populate campaign filter dropdowns in the UI.
        """
        ...
