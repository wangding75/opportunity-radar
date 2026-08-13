"""Versioned contract for classifying and evaluating opportunity risk escalation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import IntEnum, StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.core.time import as_utc_naive, utc_now

RISK_ESCALATION_CONTRACT_VERSION = "1"
RISK_ESCALATION_ALGORITHM_VERSION = "risk-escalation-v1"
RISK_ESCALATION_MAX_LOOKBACK_DAYS = 365


class RiskEscalationLevel(StrEnum):
    """Risk category derived from a bounded 0-100 risk score."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Short alias for callers that use the generic risk-level vocabulary.
RiskLevel = RiskEscalationLevel


class RiskEscalationStatus(StrEnum):
    ESCALATED = "ESCALATED"
    STABLE = "STABLE"
    DE_ESCALATED = "DE_ESCALATED"
    NO_BASELINE = "NO_BASELINE"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    INVALID_SEQUENCE = "INVALID_SEQUENCE"


class RiskEscalationPolicy(BaseModel):
    """Thresholds and compatibility rules for one risk comparison."""

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="risk-escalation-policy-v1", min_length=1, max_length=50)
    absolute_threshold: float = Field(default=10.0, ge=0.0, le=100.0)
    relative_threshold: float = Field(default=0.25, ge=0.0, le=100.0)
    max_lookback_days: int = Field(default=90, ge=1, le=RISK_ESCALATION_MAX_LOOKBACK_DAYS)
    low_threshold: float = Field(default=20.0, ge=0.0, le=100.0)
    medium_threshold: float = Field(default=40.0, ge=0.0, le=100.0)
    high_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    critical_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    require_same_model_version: bool = True
    require_same_opportunity: bool = True

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "RiskEscalationPolicy":
        thresholds = (self.low_threshold, self.medium_threshold, self.high_threshold, self.critical_threshold)
        if tuple(sorted(thresholds)) != thresholds:
            raise ValueError("risk level thresholds must be non-decreasing")
        return self


class RiskSnapshotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: int = Field(ge=1)
    model_version: str = Field(min_length=1, max_length=40)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    risk_score: float = Field(ge=0.0, le=100.0)
    stage: str = Field(min_length=1, max_length=40)
    evidence_count: int = Field(ge=0)
    breakdown: dict = Field(default_factory=dict)
    calculated_at: datetime

    @field_validator("calculated_at", mode="before")
    @classmethod
    def normalize_calculated_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("calculated_at must be a datetime")
        return as_utc_naive(value)


class RiskEscalationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: int = Field(ge=1)
    previous: RiskSnapshotInput | None = None
    current: RiskSnapshotInput


class RiskEscalationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = RISK_ESCALATION_CONTRACT_VERSION
    algorithm_version: str = RISK_ESCALATION_ALGORITHM_VERSION
    evaluated_at: datetime
    policy: RiskEscalationPolicy
    opportunity_id: int = Field(ge=1)
    status: RiskEscalationStatus
    escalated: bool
    previous_risk_score: float | None = Field(default=None, ge=0.0, le=100.0)
    current_risk_score: float = Field(ge=0.0, le=100.0)
    absolute_delta: float | None = None
    relative_delta: float | None = None
    previous_level: RiskEscalationLevel | None = None
    current_level: RiskEscalationLevel
    previous_model_version: str | None = None
    current_model_version: str
    previous_calculated_at: datetime | None = None
    current_calculated_at: datetime
    reasons: list[str] = Field(default_factory=list, min_length=1, max_length=20)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class _RiskLevelRank(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


def classify_risk_level(risk_score: float, *, policy: RiskEscalationPolicy | None = None) -> RiskEscalationLevel:
    """Map a validated risk score to a stable policy-defined severity level."""

    policy = policy or RiskEscalationPolicy()
    value = float(risk_score)
    if value < policy.low_threshold:
        return RiskEscalationLevel.NONE
    if value < policy.medium_threshold:
        return RiskEscalationLevel.LOW
    if value < policy.high_threshold:
        return RiskEscalationLevel.MEDIUM
    if value < policy.critical_threshold:
        return RiskEscalationLevel.HIGH
    return RiskEscalationLevel.CRITICAL


def _signature(input: RiskEscalationInput, policy: RiskEscalationPolicy) -> str:
    payload = {
        "contract_version": RISK_ESCALATION_CONTRACT_VERSION,
        "algorithm_version": RISK_ESCALATION_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "input": input.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_risk_escalation(
    input: RiskEscalationInput,
    *,
    policy: RiskEscalationPolicy | None = None,
    evaluated_at: datetime | None = None,
) -> RiskEscalationEvaluation:
    """Compare two compatible risk snapshots and fail closed on invalid history."""

    policy = policy or RiskEscalationPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    current = input.current
    previous = input.previous
    current_level = classify_risk_level(current.risk_score, policy=policy)
    previous_level = classify_risk_level(previous.risk_score, policy=policy) if previous else None
    status = RiskEscalationStatus.STABLE
    escalated = False
    absolute_delta = None
    relative_delta = None
    reasons: list[str] = []

    if current.opportunity_id != input.opportunity_id or (
        policy.require_same_opportunity and previous is not None and previous.opportunity_id != input.opportunity_id
    ):
        status = RiskEscalationStatus.INVALID_SEQUENCE
        reasons.append("snapshot opportunity_id does not match comparison opportunity")
    elif previous is None:
        status = RiskEscalationStatus.NO_BASELINE
        reasons.append("no previous risk snapshot is available")
    elif policy.require_same_model_version and previous.model_version != current.model_version:
        status = RiskEscalationStatus.VERSION_MISMATCH
        reasons.append(f"model version changed from {previous.model_version} to {current.model_version}")
    elif current.calculated_at <= previous.calculated_at:
        status = RiskEscalationStatus.INVALID_SEQUENCE
        reasons.append("current risk snapshot must be later than previous snapshot")
    elif current.calculated_at - previous.calculated_at > timedelta(days=policy.max_lookback_days):
        status = RiskEscalationStatus.INVALID_SEQUENCE
        reasons.append(f"risk snapshot gap exceeds {policy.max_lookback_days} days")
    else:
        absolute_delta = round(current.risk_score - previous.risk_score, 6)
        relative_delta = round(absolute_delta / max(abs(previous.risk_score), 1.0), 6)
        level_delta = _RiskLevelRank[current_level.name] - _RiskLevelRank[previous_level.name]
        threshold_escalation = absolute_delta >= policy.absolute_threshold and relative_delta >= policy.relative_threshold
        threshold_deescalation = absolute_delta <= -policy.absolute_threshold
        escalated = level_delta > 0 or threshold_escalation
        if escalated:
            status = RiskEscalationStatus.ESCALATED
        elif level_delta < 0 or threshold_deescalation:
            status = RiskEscalationStatus.DE_ESCALATED
        else:
            status = RiskEscalationStatus.STABLE
        reasons.append(f"risk level {previous_level.value} -> {current_level.value}")
        reasons.append(f"absolute delta {absolute_delta:g} {'meets' if threshold_escalation else 'below'} escalation threshold {policy.absolute_threshold:g}")
        reasons.append(f"relative delta {relative_delta:g} {'meets' if relative_delta >= policy.relative_threshold else 'below'} threshold {policy.relative_threshold:g}")
        if status == RiskEscalationStatus.ESCALATED:
            reasons.append("risk escalation passed level or threshold checks")
        elif status == RiskEscalationStatus.DE_ESCALATED:
            reasons.append("risk decreased below the prior level or threshold")

    return RiskEscalationEvaluation(
        evaluated_at=now,
        policy=policy,
        opportunity_id=input.opportunity_id,
        status=status,
        escalated=escalated,
        previous_risk_score=previous.risk_score if previous else None,
        current_risk_score=current.risk_score,
        absolute_delta=absolute_delta,
        relative_delta=relative_delta,
        previous_level=previous_level,
        current_level=current_level,
        previous_model_version=previous.model_version if previous else None,
        current_model_version=current.model_version,
        previous_calculated_at=previous.calculated_at if previous else None,
        current_calculated_at=current.calculated_at,
        reasons=reasons,
        input_signature=_signature(input, policy),
    )
