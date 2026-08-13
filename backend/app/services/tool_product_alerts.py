"""Materialize first-tool/product alerts from stable occurrence evidence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, ToolProductEntity, ToolProductOccurrence
from app.domain.alert_lifecycle import AlertPriority
from app.domain.tool_product import TOOL_PRODUCT_ALGORITHM_VERSION, TOOL_PRODUCT_CONTRACT_VERSION
from app.services.locks import acquire_alert_evaluation_lock
from app.services.tool_product_occurrences import FIRST_SEEN, materialize_tool_product_occurrences

NEW_TOOL_RULE_NAME = "NEW_TOOL"


def _ensure_new_tool_rule(db: Session, *, now: datetime) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == NEW_TOOL_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=NEW_TOOL_RULE_NAME,
            enabled=True,
            min_score=0.0,
            max_risk_score=100.0,
            min_evidence_count=1,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=0,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)
        db.flush()
    return rule


def materialize_tool_product_alerts(
    db: Session,
    *,
    entity_keys: set[str] | None = None,
    limit: int = 500,
    detected_at: datetime | None = None,
) -> dict:
    """Create one evidence-backed NEW_TOOL event per first occurrence."""

    acquire_alert_evaluation_lock(db)
    now = detected_at or utc_now()
    occurrence_result = materialize_tool_product_occurrences(
        db,
        entity_keys=entity_keys,
        limit=limit,
        detected_at=now,
    )
    stmt = (
        select(ToolProductOccurrence, ToolProductEntity)
        .join(ToolProductEntity, ToolProductEntity.id == ToolProductOccurrence.entity_id)
        .where(
            ToolProductOccurrence.classification == FIRST_SEEN,
            ToolProductOccurrence.alert_event_id.is_(None),
        )
        .order_by(ToolProductOccurrence.observed_at.asc(), ToolProductOccurrence.id.asc())
        .limit(limit)
    )
    if entity_keys is not None:
        if not entity_keys:
            return {"rule": NEW_TOOL_RULE_NAME, "evaluated": 0, "created": 0, "linked": 0, "occurrences": occurrence_result}
        stmt = stmt.where(ToolProductEntity.entity_key.in_(entity_keys))
    candidates = db.execute(stmt).all()
    if not candidates:
        return {"rule": NEW_TOOL_RULE_NAME, "evaluated": 0, "created": 0, "linked": 0, "occurrences": occurrence_result}
    rule = _ensure_new_tool_rule(db, now=now)
    created = 0
    linked = 0
    for occurrence, entity in candidates:
        existing = db.scalar(select(AlertEvent).where(AlertEvent.event_key == occurrence.occurrence_key))
        if existing is not None:
            occurrence.alert_event_id = existing.id
            linked += 1
            continue
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=None,
            keyword_id=None,
            tool_product_entity_id=entity.id,
            event_key=occurrence.occurrence_key,
            status="NEW",
            priority=AlertPriority.HIGH.value,
            title=f"New tool/product: {entity.display_name}",
            message=(
                f"First appearance detected for {entity.display_name} ({entity.kind}); "
                f"entity_key={entity.entity_key}; evidence_id={occurrence.evidence_id}; "
                f"source={occurrence.source_id}; observed_at={occurrence.observed_at.isoformat()}; "
                f"input_signature={occurrence.input_signature}; "
                f"contract_version={TOOL_PRODUCT_CONTRACT_VERSION}; "
                f"algorithm_version={TOOL_PRODUCT_ALGORITHM_VERSION}"
            )[:10_000],
            score=round(entity.confidence * 100.0, 4),
            risk_score=0.0,
            created_at=now,
        )
        db.add(event)
        db.flush()
        occurrence.alert_event_id = event.id
        created += 1
    rule.last_evaluated_at = now
    rule.updated_at = now
    db.flush()
    return {
        "rule": NEW_TOOL_RULE_NAME,
        "evaluated": len(candidates),
        "created": created,
        "linked": linked,
        "occurrences": occurrence_result,
    }
