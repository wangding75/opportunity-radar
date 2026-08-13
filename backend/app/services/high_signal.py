"""Deterministic high-signal eligibility evaluation."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.time import as_utc_naive, utc_now
from app.db.models import Opportunity
from app.domain.high_signal import (
    HighSignalEvaluation,
    HighSignalInput,
    HighSignalTriggerPolicy,
    high_signal_dedupe_key,
)


def high_signal_input_from_opportunity(opportunity: Opportunity) -> HighSignalInput:
    return HighSignalInput(
        opportunity_id=opportunity.id,
        opportunity_key=opportunity.opportunity_key,
        title=opportunity.title,
        stage=opportunity.stage,
        score=opportunity.score,
        risk_score=opportunity.risk_score,
        evidence_count=opportunity.evidence_count,
        cross_source_score=opportunity.cross_source_score,
        analysis_status=opportunity.analysis_status,
        analysis_signature=opportunity.analysis_signature or "",
        score_version=opportunity.score_version,
        updated_at=opportunity.updated_at,
    )


def evaluate_high_signal(
    input: HighSignalInput,
    *,
    now: datetime | None = None,
    policy: HighSignalTriggerPolicy | None = None,
) -> HighSignalEvaluation:
    """Evaluate all trigger conditions and retain every failed reason."""

    policy = policy or HighSignalTriggerPolicy()
    evaluated_at = as_utc_naive(now or utc_now())
    failed: list[str] = []
    reasons: list[str] = []
    stage = input.stage.upper()
    analysis_status = input.analysis_status.upper()
    age = evaluated_at - input.updated_at
    if stage in policy.excluded_stages:
        failed.append(f"stage {stage} is excluded")
    else:
        reasons.append(f"stage {stage} is eligible")
    if input.score < policy.min_score:
        failed.append(f"score {input.score:g} < {policy.min_score:g}")
    else:
        reasons.append(f"score {input.score:g} >= {policy.min_score:g}")
    if input.risk_score > policy.max_risk_score:
        failed.append(f"risk score {input.risk_score:g} > {policy.max_risk_score:g}")
    else:
        reasons.append(f"risk score {input.risk_score:g} <= {policy.max_risk_score:g}")
    if input.evidence_count < policy.min_evidence_count:
        failed.append(f"evidence count {input.evidence_count} < {policy.min_evidence_count}")
    else:
        reasons.append(f"evidence count {input.evidence_count} >= {policy.min_evidence_count}")
    if input.cross_source_score < policy.min_cross_source_score:
        failed.append(f"cross-source score {input.cross_source_score:g} < {policy.min_cross_source_score:g}")
    else:
        reasons.append(f"cross-source score {input.cross_source_score:g} >= {policy.min_cross_source_score:g}")
    if analysis_status not in policy.allowed_analysis_statuses:
        failed.append(f"analysis status {analysis_status} is not eligible")
    else:
        reasons.append(f"analysis status {analysis_status} is eligible")
    if age < timedelta(0):
        failed.append("updated_at is in the future")
    elif age > timedelta(hours=policy.max_age_hours):
        failed.append(f"signal age exceeds {policy.max_age_hours} hours")
    else:
        reasons.append(f"signal age <= {policy.max_age_hours} hours")
    return HighSignalEvaluation(
        evaluated_at=evaluated_at,
        opportunity_id=input.opportunity_id,
        opportunity_key=input.opportunity_key,
        eligible=not failed,
        dedupe_key=high_signal_dedupe_key(input, policy),
        trigger_reasons=reasons if not failed else [],
        failed_conditions=failed,
        policy=policy,
        input=input,
    )


def evaluate_opportunity_high_signal(
    opportunity: Opportunity,
    *,
    now: datetime | None = None,
    policy: HighSignalTriggerPolicy | None = None,
) -> HighSignalEvaluation:
    return evaluate_high_signal(high_signal_input_from_opportunity(opportunity), now=now, policy=policy)
