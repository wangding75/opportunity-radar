"""Materialize evidence-backed AlertEvent rows for score jump records."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, Opportunity, ScoreJumpRecord
from app.domain.alert_lifecycle import derive_alert_priority
from app.services.locks import acquire_alert_evaluation_lock

SCORE_JUMP_RULE_NAME = "SCORE_JUMP"
MAX_SCORE_JUMP_ALERTS = 100


def _ensure_score_jump_rule(db: Session, *, now) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == SCORE_JUMP_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=SCORE_JUMP_RULE_NAME,
            enabled=True,
            min_score=0.0,
            max_risk_score=100.0,
            min_evidence_count=1,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=1_440,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)
        db.flush()
    return rule


def _event_key(record: ScoreJumpRecord) -> str:
    payload = f"score-jump-alert-v1:{record.opportunity_id}:{record.input_signature}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def materialize_score_jump_alerts(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    limit: int = 100,
) -> dict:
    """Create one immutable AlertEvent for each eligible persisted score jump."""

    if limit < 1 or limit > MAX_SCORE_JUMP_ALERTS:
        raise ValueError(f"limit must be between 1 and {MAX_SCORE_JUMP_ALERTS}")
    acquire_alert_evaluation_lock(db)
    if opportunity_ids is not None and not opportunity_ids:
        return {"rule": SCORE_JUMP_RULE_NAME, "evaluated": 0, "eligible": 0, "created": 0, "duplicates": 0, "evidence_missing": 0, "suppressed": 0}
    stmt = (
        select(ScoreJumpRecord, Opportunity)
        .join(Opportunity, Opportunity.id == ScoreJumpRecord.opportunity_id)
        .order_by(ScoreJumpRecord.evaluated_at.desc(), ScoreJumpRecord.id.desc())
        .limit(limit)
    )
    if opportunity_ids is not None:
        stmt = stmt.where(ScoreJumpRecord.opportunity_id.in_(opportunity_ids))
    rows = db.execute(stmt).all()
    result = {"rule": SCORE_JUMP_RULE_NAME, "evaluated": len(rows), "eligible": 0, "created": 0, "duplicates": 0, "evidence_missing": 0, "suppressed": 0}
    now = utc_now()
    rule = None
    for record, opportunity in rows:
        if record.status != SCORE_JUMP_RULE_NAME or not record.jumped:
            result["suppressed"] += 1
            continue
        result["eligible"] += 1
        if record.alert_event_id is not None:
            result["duplicates"] += 1
            continue
        evidence_ids = record.evidence_ids or []
        evidence = record.evidence or []
        if not evidence_ids or not evidence or set(evidence_ids) != {row.get("evidence_id") for row in evidence}:
            result["evidence_missing"] += 1
            continue
        if rule is None:
            rule = _ensure_score_jump_rule(db, now=now)
        if not rule.enabled:
            result["suppressed"] += 1
            continue
        event_key = _event_key(record)
        existing = db.scalar(select(AlertEvent).where(AlertEvent.event_key == event_key))
        if existing is not None:
            record.alert_event_id = existing.id
            result["duplicates"] += 1
            continue
        evidence_text = ",".join(evidence_ids)
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=record.opportunity_id,
            keyword_id=opportunity.keyword_id,
            event_key=event_key,
            status="NEW",
            priority=derive_alert_priority(
                score=record.current_score,
                risk_score=float(opportunity.risk_score or 0.0),
                evidence_count=len(evidence_ids),
            ),
            title=f"Score jump: {opportunity.title}"[:300],
            message=(
                f"Score jump for {opportunity.opportunity_key}; previous_score={record.previous_score}; "
                f"current_score={record.current_score}; absolute_delta={record.absolute_delta}; "
                f"relative_delta={record.relative_delta}; evidence_ids={evidence_text}; "
                f"input_signature={record.input_signature}; alert_event_key={event_key}"
            )[:10_000],
            score=record.current_score,
            risk_score=float(opportunity.risk_score or 0.0),
            created_at=record.evaluated_at,
        )
        db.add(event)
        db.flush()
        record.alert_event_id = event.id
        result["created"] += 1
    if rule is not None:
        rule.last_evaluated_at = now
        rule.updated_at = now
    db.flush()
    return result
