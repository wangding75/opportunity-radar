"""Versioned contract for detecting anomalous keyword observation bursts."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now


KEYWORD_BURST_CONTRACT_VERSION = "1"
KEYWORD_BURST_ALGORITHM_VERSION = "keyword-burst-v1"
KEYWORD_BURST_TIMEZONE = "UTC"
KEYWORD_BURST_MAX_BASELINE_DAYS = 90


class BurstComparison(StrEnum):
    NEW_SIGNAL = "NEW_SIGNAL"
    BURST = "BURST"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class KeywordBurstPolicy(BaseModel):
    """Bounded, explicit thresholds for one burst evaluation."""

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="keyword-burst-policy-v1", min_length=1, max_length=50)
    current_window_days: int = Field(default=7, ge=1, le=30)
    baseline_window_days: int = Field(default=28, ge=1, le=90)
    min_current_observations: int = Field(default=5, ge=1, le=100_000)
    min_absolute_delta: int = Field(default=3, ge=0, le=100_000)
    min_growth_rate: float = Field(default=0.5, ge=0.0, le=100.0)
    min_z_score: float = Field(default=2.0, ge=0.0, le=20.0)
    include_new_signals: bool = True
    min_current_sources: int = Field(default=1, ge=0, le=100_000)

    @model_validator(mode="after")
    def validate_windows(self) -> "KeywordBurstPolicy":
        if self.baseline_window_days < self.current_window_days:
            raise ValueError("baseline_window_days must be >= current_window_days")
        if self.baseline_window_days + self.current_window_days > KEYWORD_BURST_MAX_BASELINE_DAYS:
            raise ValueError("burst windows exceed the bounded baseline horizon")
        return self


class KeywordBurstInput(BaseModel):
    """Daily points used by the detector; missing dates are treated as zero."""

    model_config = ConfigDict(extra="forbid")

    keyword_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    window_end: date
    daily_observations: dict[date, int] = Field(default_factory=dict)
    daily_sources: dict[date, int] = Field(default_factory=dict)

    @field_validator("daily_observations", "daily_sources")
    @classmethod
    def validate_daily_values(cls, values: dict[date, int]) -> dict[date, int]:
        if len(values) > KEYWORD_BURST_MAX_BASELINE_DAYS:
            raise ValueError("daily points exceed the bounded burst horizon")
        if any(int(value) < 0 for value in values.values()):
            raise ValueError("daily counts cannot be negative")
        return {day: int(value) for day, value in values.items()}


class KeywordBurstEvaluation(BaseModel):
    """Auditable output for one keyword and one complete evaluation window."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = KEYWORD_BURST_CONTRACT_VERSION
    algorithm_version: str = KEYWORD_BURST_ALGORITHM_VERSION
    timezone: str = KEYWORD_BURST_TIMEZONE
    policy: KeywordBurstPolicy
    keyword_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date
    current_observations: int = Field(ge=0)
    baseline_observations: int = Field(ge=0)
    current_sources: int = Field(ge=0)
    baseline_sources: int = Field(ge=0)
    baseline_mean_daily: float = Field(ge=0.0)
    baseline_stddev_daily: float = Field(ge=0.0)
    current_mean_daily: float = Field(ge=0.0)
    growth_rate: float | None = Field(default=None, ge=-1.0, le=100.0)
    absolute_delta: int
    z_score: float = Field(ge=0.0)
    comparison: BurstComparison
    anomalous: bool
    reasons: list[str] = Field(default_factory=list, min_length=1, max_length=12)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    evaluated_at: datetime

    @field_validator("evaluated_at", mode="before")
    @classmethod
    def normalize_evaluated_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("evaluated_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_window_math(self) -> "KeywordBurstEvaluation":
        if self.current_end != self.current_start + timedelta(days=self.policy.current_window_days):
            raise ValueError("current window must match current_window_days")
        if self.baseline_end != self.current_start or self.baseline_start != self.baseline_end - timedelta(days=self.policy.baseline_window_days):
            raise ValueError("baseline must immediately precede the current window")
        if self.absolute_delta != self.current_observations - self.baseline_observations:
            raise ValueError("absolute_delta must equal current_observations - baseline_observations")
        if self.comparison == BurstComparison.NEW_SIGNAL and self.baseline_observations != 0:
            raise ValueError("NEW_SIGNAL requires zero baseline observations")
        if self.comparison != BurstComparison.NEW_SIGNAL and self.baseline_observations == 0:
            raise ValueError("zero baseline observations require NEW_SIGNAL")
        return self


def burst_windows(window_end: date, policy: KeywordBurstPolicy) -> tuple[date, date, date, date]:
    """Return half-open current and immediately preceding baseline windows."""

    current_end = window_end
    current_start = current_end - timedelta(days=policy.current_window_days)
    baseline_end = current_start
    baseline_start = baseline_end - timedelta(days=policy.baseline_window_days)
    return current_start, current_end, baseline_start, baseline_end


def _daily_values(points: Mapping[date, int], *, start: date, end: date) -> list[int]:
    return [max(0, int(points.get(start + timedelta(days=offset), 0))) for offset in range((end - start).days)]


def _mean(values: Iterable[int]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[int], mean: float) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def build_keyword_burst_input_signature(input: KeywordBurstInput, policy: KeywordBurstPolicy) -> str:
    payload = {
        "contract_version": KEYWORD_BURST_CONTRACT_VERSION,
        "algorithm_version": KEYWORD_BURST_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "keyword_id": input.keyword_id,
        "keyword": input.keyword,
        "window_end": input.window_end.isoformat(),
        "daily_observations": sorted((day.isoformat(), int(value)) for day, value in input.daily_observations.items()),
        "daily_sources": sorted((day.isoformat(), int(value)) for day, value in input.daily_sources.items()),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_keyword_burst(
    input: KeywordBurstInput,
    *,
    policy: KeywordBurstPolicy | None = None,
    evaluated_at: datetime | None = None,
) -> KeywordBurstEvaluation:
    """Evaluate a bounded burst window, failing closed on insufficient signal."""

    policy = policy or KeywordBurstPolicy()
    current_start, current_end, baseline_start, baseline_end = burst_windows(input.window_end, policy)
    current_values = _daily_values(input.daily_observations, start=current_start, end=current_end)
    baseline_values = _daily_values(input.daily_observations, start=baseline_start, end=baseline_end)
    current_observations = sum(current_values)
    baseline_observations = sum(baseline_values)
    current_sources = max((int(input.daily_sources.get(current_start + timedelta(days=offset), 0)) for offset in range(policy.current_window_days)), default=0)
    baseline_sources = max((int(input.daily_sources.get(baseline_start + timedelta(days=offset), 0)) for offset in range(policy.baseline_window_days)), default=0)
    baseline_mean = _mean(baseline_values)
    baseline_stddev = _stddev(baseline_values, baseline_mean)
    current_mean = _mean(current_values)
    growth_rate = None if baseline_observations == 0 else (current_observations - baseline_observations) / baseline_observations
    absolute_delta = current_observations - baseline_observations
    z_score = max(0.0, (current_mean - baseline_mean) / baseline_stddev) if baseline_stddev > 0 else (float("inf") if current_mean > baseline_mean else 0.0)
    if baseline_observations == 0:
        comparison = BurstComparison.NEW_SIGNAL
    elif absolute_delta > 0:
        comparison = BurstComparison.BURST if current_mean > baseline_mean else BurstComparison.STABLE
    elif absolute_delta < 0:
        comparison = BurstComparison.DECLINING
    else:
        comparison = BurstComparison.STABLE
    reasons = [f"current observations {current_observations} over {policy.current_window_days} days"]
    anomalous = True
    if baseline_observations == 0:
        anomalous = policy.include_new_signals and current_observations >= policy.min_current_observations and current_sources >= policy.min_current_sources
        reasons.append("zero baseline treated as a new signal")
    else:
        if current_observations < policy.min_current_observations:
            anomalous = False
            reasons.append(f"current observations below {policy.min_current_observations}")
        if absolute_delta < policy.min_absolute_delta:
            anomalous = False
            reasons.append(f"absolute delta below {policy.min_absolute_delta}")
        if (growth_rate or 0.0) < policy.min_growth_rate:
            anomalous = False
            reasons.append(f"growth rate below {policy.min_growth_rate:g}")
        if z_score < policy.min_z_score:
            anomalous = False
            reasons.append(f"z-score below {policy.min_z_score:g}")
        if current_sources < policy.min_current_sources:
            anomalous = False
            reasons.append(f"current sources below {policy.min_current_sources}")
        if anomalous:
            reasons.extend([f"growth rate {growth_rate:.4g} meets threshold", f"z-score {z_score:.4g} meets threshold"])
    return KeywordBurstEvaluation(
        policy=policy,
        keyword_id=input.keyword_id,
        keyword=input.keyword,
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        current_observations=current_observations,
        baseline_observations=baseline_observations,
        current_sources=current_sources,
        baseline_sources=baseline_sources,
        baseline_mean_daily=round(baseline_mean, 6),
        baseline_stddev_daily=round(baseline_stddev, 6),
        current_mean_daily=round(current_mean, 6),
        growth_rate=None if growth_rate is None else round(growth_rate, 6),
        absolute_delta=absolute_delta,
        z_score=round(z_score, 6) if math.isfinite(z_score) else 100.0,
        comparison=comparison,
        anomalous=anomalous,
        reasons=reasons,
        input_signature=build_keyword_burst_input_signature(input, policy),
        evaluated_at=evaluated_at or utc_now(),
    )
