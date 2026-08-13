"""Versioned contract for high-signal alert eligibility and deduplication."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive

HIGH_SIGNAL_CONTRACT_VERSION = "1"
HIGH_SIGNAL_ALGORITHM_VERSION = "high-signal-v1"


class HighSignalTriggerPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="high-signal-policy-v1", min_length=1, max_length=50)
    min_score: float = Field(default=80.0, ge=0.0, le=100.0)
    max_risk_score: float = Field(default=40.0, ge=0.0, le=100.0)
    min_evidence_count: int = Field(default=3, ge=1, le=100_000)
    min_cross_source_score: float = Field(default=5.0, ge=0.0, le=20.0)
    max_age_hours: int = Field(default=48, ge=1, le=24 * 365)
    cooldown_minutes: int = Field(default=1_440, ge=1, le=525_600)
    excluded_stages: list[str] = Field(default_factory=lambda: ["DORMANT"], max_length=20)
    allowed_analysis_statuses: list[str] = Field(default_factory=lambda: ["READY", "DEGRADED"], min_length=1, max_length=10)

    @field_validator("excluded_stages", "allowed_analysis_statuses", mode="before")
    @classmethod
    def normalize_statuses(cls, values: list[str]) -> list[str]:
        return sorted({str(value).strip().upper() for value in values if str(value).strip()})


class HighSignalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: int = Field(ge=1)
    opportunity_key: str = Field(min_length=1, max_length=240)
    title: str = Field(default="", max_length=300)
    stage: str = Field(min_length=1, max_length=40)
    score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    evidence_count: int = Field(ge=0, le=100_000)
    cross_source_score: float = Field(ge=0.0, le=100.0)
    analysis_status: str = Field(min_length=1, max_length=30)
    analysis_signature: str = Field(default="", max_length=64)
    score_version: str = Field(default="score-v1", min_length=1, max_length=40)
    updated_at: datetime

    @field_validator("updated_at", mode="before")
    @classmethod
    def normalize_updated_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("updated_at must be an ISO datetime") from exc
        if not isinstance(value, datetime):
            raise ValueError("updated_at must be a datetime")
        return as_utc_naive(value)


class HighSignalEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = HIGH_SIGNAL_CONTRACT_VERSION
    algorithm_version: str = HIGH_SIGNAL_ALGORITHM_VERSION
    evaluated_at: datetime
    opportunity_id: int = Field(ge=1)
    opportunity_key: str = Field(min_length=1, max_length=240)
    eligible: bool
    dedupe_key: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    trigger_reasons: list[str] = Field(default_factory=list, max_length=20)
    failed_conditions: list[str] = Field(default_factory=list, max_length=20)
    policy: HighSignalTriggerPolicy
    input: HighSignalInput

    @field_validator("evaluated_at", mode="before")
    @classmethod
    def normalize_evaluated_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("evaluated_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_reasons(self) -> "HighSignalEvaluation":
        if self.eligible and self.failed_conditions:
            raise ValueError("eligible evaluations cannot contain failed conditions")
        if not self.eligible and not self.failed_conditions:
            raise ValueError("ineligible evaluations must explain failed conditions")
        if any(not reason.strip() for reason in [*self.trigger_reasons, *self.failed_conditions]):
            raise ValueError("evaluation reasons must not be empty")
        return self


def high_signal_dedupe_key(input: HighSignalInput, policy: HighSignalTriggerPolicy) -> str:
    """Return a stable key for the same meaningful opportunity signal state."""

    payload = {
        "contract_version": HIGH_SIGNAL_CONTRACT_VERSION,
        "algorithm_version": HIGH_SIGNAL_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "opportunity_key": input.opportunity_key,
        "score_version": input.score_version,
        "analysis_signature": input.analysis_signature,
        "stage": input.stage.upper(),
        "score": round(input.score, 4),
        "risk_score": round(input.risk_score, 4),
        "evidence_count": input.evidence_count,
        "cross_source_score": round(input.cross_source_score, 4),
        "analysis_status": input.analysis_status.upper(),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_high_signal_dedupe_key(input: HighSignalInput, policy: HighSignalTriggerPolicy) -> str:
    """Named builder alias for callers that treat the key as a derived artifact."""

    return high_signal_dedupe_key(input, policy)


def high_signal_input_from_mapping(values: Mapping[str, Any]) -> HighSignalInput:
    """Validate a persistence/API mapping without coupling the domain to ORM."""

    return HighSignalInput.model_validate(values)
