"""Versioned score contract for cross-source confirmation alert delivery."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field

CROSS_SOURCE_SCORE_CONTRACT_VERSION = "1"
CROSS_SOURCE_SCORE_ALGORITHM_VERSION = "cross-source-score-v1"


class CrossSourceScorePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="cross-source-score-policy-v1", min_length=1, max_length=50)
    min_alert_score: float = Field(default=70.0, ge=0.0, le=100.0)
    max_alert_risk: float = Field(default=40.0, ge=0.0, le=100.0)
    min_independent_sources: int = Field(default=2, ge=1, le=100)
    min_unique_claims: int = Field(default=2, ge=1, le=100)


class CrossSourceScoreInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_status: str = Field(min_length=1, max_length=30)
    confirmed: bool
    independent_source_count: int = Field(ge=0)
    unique_claim_count: int = Field(ge=0)
    fresh_evidence_count: int = Field(ge=0)
    deduplicated_evidence_count: int = Field(ge=0)
    stale_evidence_count: int = Field(ge=0)
    future_evidence_count: int = Field(ge=0)


class CrossSourceScoreEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = CROSS_SOURCE_SCORE_CONTRACT_VERSION
    algorithm_version: str = CROSS_SOURCE_SCORE_ALGORITHM_VERSION
    policy: CrossSourceScorePolicy
    input: CrossSourceScoreInput
    score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    eligible: bool
    breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list, min_length=1, max_length=20)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def score_cross_source_confirmation(
    input: CrossSourceScoreInput,
    *,
    policy: CrossSourceScorePolicy | None = None,
) -> CrossSourceScoreEvaluation:
    """Score only confirmed, independently sourced claims; otherwise suppress."""

    policy = policy or CrossSourceScorePolicy()
    source_component = min(40.0, input.independent_source_count * 20.0)
    claim_component = min(30.0, input.unique_claim_count * 15.0)
    fresh_component = min(20.0, input.fresh_evidence_count * 5.0)
    duplicate_penalty = min(20.0, input.deduplicated_evidence_count * 4.0)
    stale_penalty = min(20.0, input.stale_evidence_count * 3.0)
    future_penalty = min(30.0, input.future_evidence_count * 10.0)
    score = round(max(0.0, min(100.0, source_component + claim_component + fresh_component - duplicate_penalty - stale_penalty - future_penalty)), 4)
    risk_score = round(min(100.0, input.deduplicated_evidence_count * 5.0 + input.stale_evidence_count * 4.0 + input.future_evidence_count * 20.0 + (0.0 if input.confirmed else 30.0)), 4)
    eligible = (
        input.confirmed
        and input.confirmation_status.upper() == "CONFIRMED"
        and input.independent_source_count >= policy.min_independent_sources
        and input.unique_claim_count >= policy.min_unique_claims
        and score >= policy.min_alert_score
        and risk_score <= policy.max_alert_risk
    )
    reasons = [
        f"score {score:g} {'meets' if score >= policy.min_alert_score else 'below'} alert threshold {policy.min_alert_score:g}",
        f"risk {risk_score:g} {'within' if risk_score <= policy.max_alert_risk else 'above'} limit {policy.max_alert_risk:g}",
    ]
    if eligible:
        reasons.append("confirmed claims are eligible for alert delivery")
    else:
        reasons.append("cross-source confirmation is suppressed until all delivery gates pass")
    breakdown = {
        "source_component": source_component,
        "claim_component": claim_component,
        "fresh_component": fresh_component,
        "duplicate_penalty": duplicate_penalty,
        "stale_penalty": stale_penalty,
        "future_penalty": future_penalty,
    }
    signature_payload = {
        "contract_version": CROSS_SOURCE_SCORE_CONTRACT_VERSION,
        "algorithm_version": CROSS_SOURCE_SCORE_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "input": input.model_dump(mode="json"),
        "score": score,
        "risk_score": risk_score,
    }
    signature = hashlib.sha256(json.dumps(signature_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return CrossSourceScoreEvaluation(
        policy=policy,
        input=input,
        score=score,
        risk_score=risk_score,
        eligible=eligible,
        breakdown=breakdown,
        reasons=reasons,
        input_signature=signature,
    )
