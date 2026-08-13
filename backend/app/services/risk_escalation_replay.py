"""Bounded, read-only replay for persisted risk escalation inputs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive
from app.db.models import Opportunity, OpportunityScoreSnapshot
from app.domain.risk_escalation import RiskEscalationInput, RiskEscalationPolicy, evaluate_risk_escalation
from app.services.risk_escalation import _snapshot_input
from app.services.risk_escalation_alerts import _change_breakdown, _evidence_for_escalation


def replay_risk_escalation(
    db: Session,
    opportunity_id: int,
    *,
    as_of: datetime,
    policy: RiskEscalationPolicy | None = None,
) -> dict | None:
    """Evaluate the latest two persisted snapshots at or before ``as_of`` without writes."""

    if db.get(Opportunity, opportunity_id) is None:
        raise KeyError(f"unknown opportunity id: {opportunity_id}")
    as_of = as_utc_naive(as_of)
    rows = db.scalars(
        select(OpportunityScoreSnapshot)
        .where(OpportunityScoreSnapshot.opportunity_id == opportunity_id, OpportunityScoreSnapshot.calculated_at <= as_of)
        .order_by(OpportunityScoreSnapshot.calculated_at.desc(), OpportunityScoreSnapshot.id.desc())
        .limit(2)
    ).all()
    if not rows:
        return None
    current = _snapshot_input(rows[0])
    previous = _snapshot_input(rows[1]) if len(rows) > 1 else None
    evaluation = evaluate_risk_escalation(
        RiskEscalationInput(opportunity_id=opportunity_id, previous=previous, current=current),
        policy=policy,
        evaluated_at=as_of,
    )
    evidence = _evidence_for_escalation(db, opportunity_id, previous_at=previous.calculated_at if previous else None, current_at=current.calculated_at)
    return {
        **evaluation.model_dump(mode="json"),
        "previous_breakdown": previous.breakdown if previous else {},
        "current_breakdown": current.breakdown,
        "change_breakdown": _change_breakdown(evaluation, current=current, previous=previous),
        "evidence_ids": [row["evidence_id"] for row in evidence],
        "evidence": evidence,
        "replay_mode": "persisted_risk_escalation_evaluation",
        "read_only": True,
    }
