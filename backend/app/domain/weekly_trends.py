"""Versioned contract for weekly emerging-trend reports."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any, Iterable, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive


WEEKLY_TREND_CONTRACT_VERSION = "1"
WEEKLY_TREND_ALGORITHM_VERSION = "weekly-trend-v1"
WEEKLY_TREND_TIMEZONE = "UTC"
WEEKLY_TREND_MAX_ITEMS = 20
WEEKLY_TREND_MAX_CANDIDATES = 100


class WeeklyTrendStatus(StrEnum):
    READY = "READY"
    EMPTY = "EMPTY"
    DEGRADED = "DEGRADED"


class TrendComparison(StrEnum):
    NEW_SIGNAL = "NEW_SIGNAL"
    GROWING = "GROWING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class TrendEvidenceProvenance(StrEnum):
    OBSERVED = "OBSERVED"
    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"
    MIXED = "MIXED"


class WeeklyTrendPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="weekly-trend-selection-v1", min_length=1, max_length=50)
    min_current_observations: int = Field(default=3, ge=1, le=100_000)
    min_absolute_delta: int = Field(default=1, ge=0, le=100_000)
    min_growth_rate: float = Field(default=0.2, ge=0.0, le=100.0)
    include_new_signals: bool = True
    max_items: int = Field(default=WEEKLY_TREND_MAX_ITEMS, ge=1, le=WEEKLY_TREND_MAX_ITEMS)
    sort_order: Literal["momentum_desc,delta_desc,current_desc,keyword_asc"] = "momentum_desc,delta_desc,current_desc,keyword_asc"


class WeeklyTrendItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1, le=WEEKLY_TREND_MAX_ITEMS)
    keyword_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    comparison: TrendComparison
    current_observations: int = Field(ge=1, le=100_000)
    baseline_observations: int = Field(ge=0, le=100_000)
    current_sources: int = Field(ge=0, le=100_000)
    baseline_sources: int = Field(ge=0, le=100_000)
    absolute_delta: int
    growth_rate: float | None = Field(default=None, ge=-1.0, le=100.0)
    momentum_score: float = Field(ge=0.0, le=100.0)
    trend_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    last_seen_at: datetime
    evidence_provenance: TrendEvidenceProvenance
    selection_reasons: list[str] = Field(min_length=1, max_length=10)

    @field_validator("last_seen_at", mode="before")
    @classmethod
    def normalize_timestamp(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("last_seen_at must be an ISO datetime") from exc
        if not isinstance(value, datetime):
            raise ValueError("last_seen_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_comparison_math(self) -> "WeeklyTrendItem":
        if self.absolute_delta != self.current_observations - self.baseline_observations:
            raise ValueError("absolute_delta must equal current_observations - baseline_observations")
        if self.baseline_observations == 0:
            if self.comparison != TrendComparison.NEW_SIGNAL or self.growth_rate is not None:
                raise ValueError("baseline-zero trends must use NEW_SIGNAL with null growth_rate")
        elif self.growth_rate is None:
            raise ValueError("growth_rate is required when baseline_observations is non-zero")
        if any(not reason.strip() for reason in self.selection_reasons):
            raise ValueError("selection_reasons must not be empty")
        return self


class WeeklyTrendReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["1"] = WEEKLY_TREND_CONTRACT_VERSION
    algorithm_version: str = Field(default=WEEKLY_TREND_ALGORITHM_VERSION, min_length=1, max_length=50)
    timezone: Literal["UTC"] = WEEKLY_TREND_TIMEZONE
    week_start: date
    week_end: date
    baseline_start: date
    baseline_end: date
    generated_at: datetime
    status: WeeklyTrendStatus
    policy: WeeklyTrendPolicy
    total_candidates: int = Field(ge=0, le=WEEKLY_TREND_MAX_CANDIDATES)
    selected_count: int = Field(ge=0, le=WEEKLY_TREND_MAX_ITEMS)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    items: list[WeeklyTrendItem] = Field(default_factory=list, max_length=WEEKLY_TREND_MAX_ITEMS)
    warnings: list[str] = Field(default_factory=list, max_length=10)
    generation_error: str | None = Field(default=None, max_length=2_000)

    @field_validator("generated_at", mode="before")
    @classmethod
    def normalize_generated_at(cls, value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError("generated_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_window_and_state(self) -> "WeeklyTrendReport":
        if self.week_start.weekday() != 0 or self.week_end != self.week_start + timedelta(days=7):
            raise ValueError("week window must be a complete Monday-to-Monday interval")
        if self.baseline_start != self.week_start - timedelta(days=7) or self.baseline_end != self.week_start:
            raise ValueError("baseline must be the immediately preceding complete week")
        if self.selected_count != len(self.items):
            raise ValueError("selected_count must equal the number of trend items")
        if self.selected_count > self.total_candidates:
            raise ValueError("selected_count cannot exceed total_candidates")
        if [item.rank for item in self.items] != list(range(1, len(self.items) + 1)):
            raise ValueError("trend item ranks must be contiguous and start at 1")
        if len({item.keyword_id for item in self.items}) != len(self.items):
            raise ValueError("trend items must not contain duplicate keyword_id values")
        if self.status == WeeklyTrendStatus.EMPTY and self.items:
            raise ValueError("EMPTY trend report must not contain items")
        if self.status == WeeklyTrendStatus.READY and not self.items:
            raise ValueError("READY trend report must contain at least one item")
        if self.status == WeeklyTrendStatus.DEGRADED and not (self.warnings or self.generation_error):
            raise ValueError("DEGRADED trend report must explain the degradation")
        if self.generation_error and self.status != WeeklyTrendStatus.DEGRADED:
            raise ValueError("generation_error requires DEGRADED status")
        return self


def completed_week_window(anchor: date) -> tuple[date, date, date, date]:
    """Return report week and immediately preceding baseline for an anchor date."""

    current_week_start = anchor - timedelta(days=anchor.weekday())
    week_end = current_week_start
    week_start = week_end - timedelta(days=7)
    return week_start, week_end, week_start - timedelta(days=7), week_start


def _canonical_bucket(row: Mapping[str, Any] | WeeklyTrendItem) -> dict[str, Any]:
    values = row.model_dump(mode="json") if isinstance(row, WeeklyTrendItem) else row
    return {
        "keyword_id": values.get("keyword_id"),
        "keyword": values.get("keyword"),
        "current_observations": values.get("current_observations"),
        "baseline_observations": values.get("baseline_observations"),
        "current_sources": values.get("current_sources"),
        "baseline_sources": values.get("baseline_sources"),
        "absolute_delta": values.get("absolute_delta"),
        "growth_rate": values.get("growth_rate"),
        "momentum_score": values.get("momentum_score"),
        "trend_signature": values.get("trend_signature"),
        "last_seen_at": values.get("last_seen_at"),
        "evidence_provenance": values.get("evidence_provenance"),
    }


def build_weekly_trend_input_signature(
    *,
    week_start: date,
    week_end: date,
    baseline_start: date,
    baseline_end: date,
    candidates: Iterable[Mapping[str, Any] | WeeklyTrendItem],
    policy: WeeklyTrendPolicy,
) -> str:
    payload = {
        "contract_version": WEEKLY_TREND_CONTRACT_VERSION,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "baseline_start": baseline_start.isoformat(),
        "baseline_end": baseline_end.isoformat(),
        "policy": policy.model_dump(mode="json"),
        "candidates": sorted(
            (_canonical_bucket(row) for row in candidates),
            key=lambda row: (int(row["keyword_id"] or 0), str(row["keyword"] or "")),
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
