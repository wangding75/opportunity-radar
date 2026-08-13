"""Versioned contract for detecting hiring-growth surges from job evidence."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now


HIRING_SURGE_CONTRACT_VERSION = "1"
HIRING_SURGE_ALGORITHM_VERSION = "hiring-surge-v1"
HIRING_SURGE_TIMEZONE = "UTC"
HIRING_SURGE_MAX_HORIZON_DAYS = 90


class HiringComparison(StrEnum):
    NEW_SIGNAL = "NEW_SIGNAL"
    SURGE = "SURGE"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class HiringSurgePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="hiring-surge-policy-v1", min_length=1, max_length=50)
    current_window_days: int = Field(default=7, ge=1, le=30)
    baseline_window_days: int = Field(default=28, ge=1, le=90)
    min_current_jobs: int = Field(default=5, ge=1, le=100_000)
    min_absolute_delta: int = Field(default=3, ge=0, le=100_000)
    min_growth_rate: float = Field(default=0.5, ge=0.0, le=100.0)
    min_z_score: float = Field(default=2.0, ge=0.0, le=20.0)
    min_current_sources: int = Field(default=1, ge=0, le=100_000)
    min_current_evidence: int = Field(default=1, ge=0, le=100_000)
    include_new_signals: bool = True

    @model_validator(mode="after")
    def validate_windows(self) -> "HiringSurgePolicy":
        if self.baseline_window_days < self.current_window_days:
            raise ValueError("baseline_window_days must be >= current_window_days")
        if self.baseline_window_days + self.current_window_days > HIRING_SURGE_MAX_HORIZON_DAYS:
            raise ValueError("hiring windows exceed the bounded horizon")
        return self


class HiringSurgeInput(BaseModel):
    """Daily job, source, and evidence counts for one keyword."""

    model_config = ConfigDict(extra="forbid")

    keyword_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    window_end: date
    daily_jobs: dict[date, int] = Field(default_factory=dict)
    daily_sources: dict[date, int] = Field(default_factory=dict)
    daily_evidence: dict[date, int] = Field(default_factory=dict)

    @field_validator("daily_jobs", "daily_sources", "daily_evidence")
    @classmethod
    def validate_daily_values(cls, values: dict[date, int]) -> dict[date, int]:
        if len(values) > HIRING_SURGE_MAX_HORIZON_DAYS:
            raise ValueError("daily points exceed the bounded hiring horizon")
        if any(int(value) < 0 for value in values.values()):
            raise ValueError("daily counts cannot be negative")
        return {day: int(value) for day, value in values.items()}


class HiringSurgeEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = HIRING_SURGE_CONTRACT_VERSION
    algorithm_version: str = HIRING_SURGE_ALGORITHM_VERSION
    timezone: str = HIRING_SURGE_TIMEZONE
    policy: HiringSurgePolicy
    keyword_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date
    current_jobs: int = Field(ge=0)
    baseline_jobs: int = Field(ge=0)
    current_sources: int = Field(ge=0)
    baseline_sources: int = Field(ge=0)
    current_evidence: int = Field(ge=0)
    baseline_evidence: int = Field(ge=0)
    baseline_mean_daily: float = Field(ge=0.0)
    baseline_stddev_daily: float = Field(ge=0.0)
    current_mean_daily: float = Field(ge=0.0)
    growth_rate: float | None = Field(default=None, ge=-1.0, le=100.0)
    absolute_delta: int
    z_score: float = Field(ge=0.0)
    comparison: HiringComparison
    surge: bool
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
    def validate_window_math(self) -> "HiringSurgeEvaluation":
        if self.current_end != self.current_start + timedelta(days=self.policy.current_window_days):
            raise ValueError("current window must match current_window_days")
        if self.baseline_end != self.current_start or self.baseline_start != self.baseline_end - timedelta(days=self.policy.baseline_window_days):
            raise ValueError("baseline must immediately precede the current window")
        if self.absolute_delta != self.current_jobs - self.baseline_jobs:
            raise ValueError("absolute_delta must equal current_jobs - baseline_jobs")
        if self.comparison == HiringComparison.NEW_SIGNAL and self.baseline_jobs != 0:
            raise ValueError("NEW_SIGNAL requires zero baseline jobs")
        if self.comparison != HiringComparison.NEW_SIGNAL and self.baseline_jobs == 0:
            raise ValueError("zero baseline jobs require NEW_SIGNAL")
        return self


class HiringDiversityMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_unique_jobs: int = Field(ge=0)
    baseline_unique_jobs: int = Field(ge=0)
    current_duplicate_observations: int = Field(ge=0)
    baseline_duplicate_observations: int = Field(ge=0)
    current_company_count: int = Field(ge=0)
    baseline_company_count: int = Field(ge=0)
    current_unknown_company_count: int = Field(ge=0)
    baseline_unknown_company_count: int = Field(ge=0)
    current_source_count: int = Field(ge=0)
    baseline_source_count: int = Field(ge=0)
    current_company_diversity: float = Field(ge=0.0, le=1.0)
    baseline_company_diversity: float = Field(ge=0.0, le=1.0)
    current_source_diversity: float = Field(ge=0.0, le=1.0)
    baseline_source_diversity: float = Field(ge=0.0, le=1.0)
    current_duplicate_rate: float = Field(ge=0.0, le=1.0)
    baseline_duplicate_rate: float = Field(ge=0.0, le=1.0)


class HiringSurgeDetection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation: HiringSurgeEvaluation
    metrics: HiringDiversityMetrics
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    detection_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def hiring_windows(window_end: date, policy: HiringSurgePolicy) -> tuple[date, date, date, date]:
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


def build_hiring_surge_input_signature(input: HiringSurgeInput, policy: HiringSurgePolicy) -> str:
    payload = {
        "contract_version": HIRING_SURGE_CONTRACT_VERSION,
        "algorithm_version": HIRING_SURGE_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "keyword_id": input.keyword_id,
        "keyword": input.keyword,
        "window_end": input.window_end.isoformat(),
        "daily_jobs": sorted((day.isoformat(), int(value)) for day, value in input.daily_jobs.items()),
        "daily_sources": sorted((day.isoformat(), int(value)) for day, value in input.daily_sources.items()),
        "daily_evidence": sorted((day.isoformat(), int(value)) for day, value in input.daily_evidence.items()),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_hiring_surge(
    input: HiringSurgeInput,
    *,
    policy: HiringSurgePolicy | None = None,
    evaluated_at: datetime | None = None,
) -> HiringSurgeEvaluation:
    """Evaluate a bounded hiring window and fail closed without enough signal."""

    policy = policy or HiringSurgePolicy()
    current_start, current_end, baseline_start, baseline_end = hiring_windows(input.window_end, policy)
    current_jobs = _daily_values(input.daily_jobs, start=current_start, end=current_end)
    baseline_jobs = _daily_values(input.daily_jobs, start=baseline_start, end=baseline_end)
    current_sources = max((int(input.daily_sources.get(current_start + timedelta(days=offset), 0)) for offset in range(policy.current_window_days)), default=0)
    baseline_sources = max((int(input.daily_sources.get(baseline_start + timedelta(days=offset), 0)) for offset in range(policy.baseline_window_days)), default=0)
    current_evidence = sum(_daily_values(input.daily_evidence, start=current_start, end=current_end))
    baseline_evidence = sum(_daily_values(input.daily_evidence, start=baseline_start, end=baseline_end))
    current_total = sum(current_jobs)
    baseline_total = sum(baseline_jobs)
    baseline_mean = _mean(baseline_jobs)
    baseline_stddev = _stddev(baseline_jobs, baseline_mean)
    current_mean = _mean(current_jobs)
    growth_rate = None if baseline_total == 0 else (current_total - baseline_total) / baseline_total
    absolute_delta = current_total - baseline_total
    z_score = max(0.0, (current_mean - baseline_mean) / baseline_stddev) if baseline_stddev > 0 else (float("inf") if current_mean > baseline_mean else 0.0)
    comparison = (
        HiringComparison.NEW_SIGNAL if baseline_total == 0 else
        HiringComparison.SURGE if current_mean > baseline_mean and absolute_delta > 0 else
        HiringComparison.DECLINING if absolute_delta < 0 else
        HiringComparison.STABLE
    )
    reasons = [f"current jobs {current_total} over {policy.current_window_days} days"]
    surge = True
    if baseline_total == 0:
        surge = policy.include_new_signals and current_total >= policy.min_current_jobs and current_sources >= policy.min_current_sources and current_evidence >= policy.min_current_evidence
        reasons.append("zero baseline jobs treated as a new hiring signal")
    else:
        checks = (
            (current_total >= policy.min_current_jobs, f"current jobs below {policy.min_current_jobs}"),
            (absolute_delta >= policy.min_absolute_delta, f"absolute delta below {policy.min_absolute_delta}"),
            ((growth_rate or 0.0) >= policy.min_growth_rate, f"growth rate below {policy.min_growth_rate:g}"),
            (z_score >= policy.min_z_score, f"z-score below {policy.min_z_score:g}"),
            (current_sources >= policy.min_current_sources, f"current sources below {policy.min_current_sources}"),
            (current_evidence >= policy.min_current_evidence, f"current evidence below {policy.min_current_evidence}"),
        )
        for passed, reason in checks:
            if not passed:
                surge = False
                reasons.append(reason)
        if surge:
            reasons.extend([f"growth rate {growth_rate:.4g} meets threshold", f"z-score {z_score:.4g} meets threshold"])
    return HiringSurgeEvaluation(
        policy=policy,
        keyword_id=input.keyword_id,
        keyword=input.keyword,
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        current_jobs=current_total,
        baseline_jobs=baseline_total,
        current_sources=current_sources,
        baseline_sources=baseline_sources,
        current_evidence=current_evidence,
        baseline_evidence=baseline_evidence,
        baseline_mean_daily=round(baseline_mean, 6),
        baseline_stddev_daily=round(baseline_stddev, 6),
        current_mean_daily=round(current_mean, 6),
        growth_rate=None if growth_rate is None else round(growth_rate, 6),
        absolute_delta=absolute_delta,
        z_score=round(z_score, 6) if math.isfinite(z_score) else 100.0,
        comparison=comparison,
        surge=surge,
        reasons=reasons,
        input_signature=build_hiring_surge_input_signature(input, policy),
        evaluated_at=evaluated_at or utc_now(),
    )
