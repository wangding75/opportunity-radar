"""Read-only risk escalation detection over persisted score snapshots."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import Opportunity, OpportunityScoreSnapshot
from app.domain.risk_escalation import RiskEscalationEvaluation, RiskEscalationInput, RiskEscalationPolicy, RiskSnapshotInput, evaluate_risk_escalation

MAX_RISK_ESCALATION_OPPORTUNITIES = 100
MAX_RISK_ESCALATION_SNAPSHOTS = 2


def _snapshot_input(row: OpportunityScoreSnapshot) -> RiskSnapshotInput:
    return RiskSnapshotInput(
        opportunity_id=row.opportunity_id,
        model_version=row.model_version,
        input_signature=row.input_signature,
        risk_score=row.risk_score,
        stage=row.stage,
        evidence_count=row.evidence_count,
        breakdown=row.breakdown or {},
        calculated_at=row.calculated_at,
    )


def _snapshots_for_opportunity(db: Session, opportunity_id: int) -> list[OpportunityScoreSnapshot]:
    return db.scalars(
        select(OpportunityScoreSnapshot)
        .where(OpportunityScoreSnapshot.opportunity_id == opportunity_id)
        .order_by(OpportunityScoreSnapshot.calculated_at.desc(), OpportunityScoreSnapshot.id.desc())
        .limit(MAX_RISK_ESCALATION_SNAPSHOTS)
    ).all()


def detect_risk_escalations(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    policy: RiskEscalationPolicy | None = None,
    escalated_only: bool = False,
    evaluated_at: datetime | None = None,
    limit: int = 100,
) -> list[RiskEscalationEvaluation]:
    """Evaluate bounded risk history without mutating records or alert state."""

    if limit < 1 or limit > MAX_RISK_ESCALATION_OPPORTUNITIES:
        raise ValueError(f"limit must be between 1 and {MAX_RISK_ESCALATION_OPPORTUNITIES}")
    if opportunity_ids is not None and not opportunity_ids:
        return []
    policy = policy or RiskEscalationPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    stmt = select(Opportunity.id).where(Opportunity.stage != "DORMANT").order_by(Opportunity.id).limit(limit)
    if opportunity_ids is not None:
        stmt = stmt.where(Opportunity.id.in_(opportunity_ids))
    selected_ids = list(db.scalars(stmt).all())
    results: list[RiskEscalationEvaluation] = []
    for opportunity_id in selected_ids:
        rows = _snapshots_for_opportunity(db, opportunity_id)
        if not rows:
            continue
        current = _snapshot_input(rows[0])
        previous = _snapshot_input(rows[1]) if len(rows) > 1 else None
        evaluation = evaluate_risk_escalation(
            RiskEscalationInput(opportunity_id=opportunity_id, previous=previous, current=current),
            policy=policy,
            evaluated_at=now,
        )
        if escalated_only and not evaluation.escalated:
            continue
        results.append(evaluation)
    return results
