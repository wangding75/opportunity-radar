"""Versioned contract for detecting opportunity score jumps."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.time import as_utc_naive, utc_now

SCORE_JUMP_CONTRACT_VERSION = "1"
SCORE_JUMP_ALGORITHM_VERSION = "score-jump-v1"
SCORE_JUMP_MAX_LOOKBACK_DAYS = 365


class ScoreJumpStatus(StrEnum):
    SCORE_JUMP = "SCORE_JUMP"
    NO_JUMP = "NO_JUMP"
    NO_BASELINE = "NO_BASELINE"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    INVALID_SEQUENCE = "INVALID_SEQUENCE"


class ScoreJumpPolicy(BaseModel):
    """Bounded thresholds and compatibility constraints for one comparison."""

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="score-jump-policy-v1", min_length=1, max_length=50)
    absolute_threshold: float = Field(default=15.0, ge=0.0, le=100.0)
    relative_threshold: float = Field(default=0.25, ge=0.0, le=100.0)
    max_lookback_days: int = Field(default=90, ge=1, le=SCORE_JUMP_MAX_LOOKBACK_DAYS)
    require_same_model_version: bool = True
    require_same_opportunity: bool = True


class ScoreSnapshotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: int = Field(ge=1)
    model_version: str = Field(min_length=1, max_length=40)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    score: float = Field(ge=0.0, le=100.0)
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


class ScoreJumpInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: int = Field(ge=1)
    previous: ScoreSnapshotInput | None = None
    current: ScoreSnapshotInput


class ScoreJumpEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = SCORE_JUMP_CONTRACT_VERSION
    algorithm_version: str = SCORE_JUMP_ALGORITHM_VERSION
    evaluated_at: datetime
    policy: ScoreJumpPolicy
    opportunity_id: int = Field(ge=1)
    status: ScoreJumpStatus
    jumped: bool
    previous_score: float | None = Field(default=None, ge=0.0, le=100.0)
    current_score: float = Field(ge=0.0, le=100.0)
    absolute_delta: float | None = None
    relative_delta: float | None = None
    previous_model_version: str | None = None
    current_model_version: str
    previous_calculated_at: datetime | None = None
    current_calculated_at: datetime
    reasons: list[str] = Field(default_factory=list, min_length=1, max_length=20)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def _signature(input: ScoreJumpInput, policy: ScoreJumpPolicy) -> str:
    payload = {
        "contract_version": SCORE_JUMP_CONTRACT_VERSION,
        "algorithm_version": SCORE_JUMP_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "input": input.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_score_jump(
    input: ScoreJumpInput,
    *,
    policy: ScoreJumpPolicy | None = None,
    evaluated_at: datetime | None = None,
) -> ScoreJumpEvaluation:
    """Compare two compatible snapshots and fail closed on missing/invalid history."""

    policy = policy or ScoreJumpPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    current = input.current
    previous = input.previous
    status = ScoreJumpStatus.NO_JUMP
    jumped = False
    absolute_delta = None
    relative_delta = None
    reasons: list[str] = []
    if current.opportunity_id != input.opportunity_id or (policy.require_same_opportunity and previous is not None and previous.opportunity_id != input.opportunity_id):
        status = ScoreJumpStatus.INVALID_SEQUENCE
        reasons.append("snapshot opportunity_id does not match comparison opportunity")
    elif previous is None:
        status = ScoreJumpStatus.NO_BASELINE
        reasons.append("no previous score snapshot is available")
    elif policy.require_same_model_version and previous.model_version != current.model_version:
        status = ScoreJumpStatus.VERSION_MISMATCH
        reasons.append(f"model version changed from {previous.model_version} to {current.model_version}")
    elif current.calculated_at <= previous.calculated_at:
        status = ScoreJumpStatus.INVALID_SEQUENCE
        reasons.append("current snapshot must be later than previous snapshot")
    elif current.calculated_at - previous.calculated_at > timedelta(days=policy.max_lookback_days):
        status = ScoreJumpStatus.INVALID_SEQUENCE
        reasons.append(f"snapshot gap exceeds {policy.max_lookback_days} days")
    else:
        absolute_delta = round(current.score - previous.score, 6)
        relative_delta = round(absolute_delta / max(abs(previous.score), 1.0), 6)
        jumped = absolute_delta >= policy.absolute_threshold and relative_delta >= policy.relative_threshold
        status = ScoreJumpStatus.SCORE_JUMP if jumped else ScoreJumpStatus.NO_JUMP
        reasons.append(f"absolute delta {absolute_delta:g} {'meets' if absolute_delta >= policy.absolute_threshold else 'below'} threshold {policy.absolute_threshold:g}")
        reasons.append(f"relative delta {relative_delta:g} {'meets' if relative_delta >= policy.relative_threshold else 'below'} threshold {policy.relative_threshold:g}")
        if jumped:
            reasons.append("score jump passed both threshold checks")
    return ScoreJumpEvaluation(
        evaluated_at=now,
        policy=policy,
        opportunity_id=input.opportunity_id,
        status=status,
        jumped=jumped,
        previous_score=previous.score if previous else None,
        current_score=current.score,
        absolute_delta=absolute_delta,
        relative_delta=relative_delta,
        previous_model_version=previous.model_version if previous else None,
        current_model_version=current.model_version,
        previous_calculated_at=previous.calculated_at if previous else None,
        current_calculated_at=current.calculated_at,
        reasons=reasons,
        input_signature=_signature(input, policy),
    )
