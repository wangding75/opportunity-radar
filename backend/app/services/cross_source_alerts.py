"""Score persisted cross-source confirmations and deliver idempotent alerts."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, CrossSourceConfirmationRecord, Opportunity
from app.domain.alert_lifecycle import AlertPriority, derive_alert_priority
from app.domain.cross_source_score import CrossSourceScoreEvaluation, CrossSourceScoreInput, CrossSourceScorePolicy, score_cross_source_confirmation
from app.services.locks import acquire_alert_evaluation_lock

CROSS_SOURCE_CONFIRMATION_RULE_NAME = "CROSS_SOURCE_CONFIRMATION"


def _ensure_cross_source_rule(db: Session, *, now) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == CROSS_SOURCE_CONFIRMATION_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=CROSS_SOURCE_CONFIRMATION_RULE_NAME,
            enabled=True,
            min_score=70.0,
            max_risk_score=40.0,
            min_evidence_count=2,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=1_440,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)
        db.flush()
    return rule


def _score_input(record: CrossSourceConfirmationRecord) -> CrossSourceScoreInput:
    return CrossSourceScoreInput(
        confirmation_status=record.status,
        confirmed=record.confirmed,
        independent_source_count=record.independent_source_count,
        unique_claim_count=record.unique_claim_count,
        fresh_evidence_count=record.fresh_evidence_count,
        deduplicated_evidence_count=record.deduplicated_evidence_count,
        stale_evidence_count=record.stale_evidence_count,
        future_evidence_count=record.future_evidence_count,
    )


def _apply_score(record: CrossSourceConfirmationRecord, score: CrossSourceScoreEvaluation) -> None:
    record.score_contract_version = score.contract_version
    record.score_algorithm_version = score.algorithm_version
    record.score_input_signature = score.input_signature
    record.score = score.score
    record.risk_score = score.risk_score
    record.score_breakdown = score.breakdown


def _alert_event_key(record: CrossSourceConfirmationRecord, score: CrossSourceScoreEvaluation) -> str:
    payload = f"cross-source-alert-v1:{record.opportunity_id}:{record.input_signature}:{score.input_signature}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def materialize_cross_source_alerts(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    policy: CrossSourceScorePolicy | None = None,
    limit: int = 100,
) -> dict:
    """Create AlertEvent rows only for score-eligible confirmation records."""

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    acquire_alert_evaluation_lock(db)
    policy = policy or CrossSourceScorePolicy()
    stmt = (
        select(CrossSourceConfirmationRecord, Opportunity)
        .join(Opportunity, Opportunity.id == CrossSourceConfirmationRecord.opportunity_id)
        .order_by(CrossSourceConfirmationRecord.evaluated_at.desc(), CrossSourceConfirmationRecord.id.desc())
        .limit(limit)
    )
    if opportunity_ids is not None:
        if not opportunity_ids:
            return {"rule": CROSS_SOURCE_CONFIRMATION_RULE_NAME, "evaluated": 0, "eligible": 0, "created": 0, "duplicates": 0, "suppressed": 0}
        stmt = stmt.where(CrossSourceConfirmationRecord.opportunity_id.in_(opportunity_ids))
    rows = db.execute(stmt).all()
    result = {"rule": CROSS_SOURCE_CONFIRMATION_RULE_NAME, "evaluated": len(rows), "eligible": 0, "created": 0, "duplicates": 0, "suppressed": 0}
    rule = None
    now = utc_now()
    for record, opportunity in rows:
        score = score_cross_source_confirmation(_score_input(record), policy=policy)
        _apply_score(record, score)
        if not score.eligible:
            result["suppressed"] += 1
            continue
        result["eligible"] += 1
        if record.alert_event_id is not None:
            result["duplicates"] += 1
            continue
        event_key = _alert_event_key(record, score)
        event = db.scalar(select(AlertEvent).where(AlertEvent.event_key == event_key))
        if event is not None:
            record.alert_event_id = event.id
            result["duplicates"] += 1
            continue
        if rule is None:
            rule = _ensure_cross_source_rule(db, now=now)
        priority = derive_alert_priority(
            score=score.score,
            risk_score=score.risk_score,
            evidence_count=record.fresh_evidence_count,
            high_signal=score.score >= 80.0 and score.risk_score <= 20.0,
        )
        evidence_ids = ",".join(record.evidence_ids or [])
        endpoints = ",".join(record.source_endpoints or [])
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=record.opportunity_id,
            keyword_id=opportunity.keyword_id,
            event_key=event_key,
            status="NEW",
            priority=priority,
            title=f"Cross-source confirmation: {opportunity.title}",
            message=(
                f"Cross-source confirmation for {opportunity.opportunity_key}; score={score.score}; risk_score={score.risk_score}; "
                f"independent_source_count={record.independent_source_count}; unique_claim_count={record.unique_claim_count}; "
                f"deduplicated_evidence_count={record.deduplicated_evidence_count}; endpoints={endpoints}; "
                f"evidence_ids={evidence_ids}; score_input_signature={score.input_signature}; alert_event_key={event_key}"
            )[:10_000],
            score=score.score,
            risk_score=score.risk_score,
            created_at=record.evaluated_at,
        )
        db.add(event)
        db.flush()
        record.alert_event_id = event.id
        result["created"] += 1
    db.flush()
    return result
