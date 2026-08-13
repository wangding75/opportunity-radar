"""Persist evidence-backed risk escalation explanations and alerts."""

from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import AlertEvent, AlertRule, NormalizedItem, Opportunity, OpportunityEvidence, RawObservation, RiskEscalationRecord
from app.domain.alert_lifecycle import derive_alert_priority
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.risk_escalation import RiskEscalationEvaluation, RiskEscalationPolicy
from app.services.locks import acquire_alert_evaluation_lock
from app.services.risk_escalation import _snapshot_input, _snapshots_for_opportunity, detect_risk_escalations

RISK_ESCALATION_RULE_NAME = "RISK_ESCALATION"
MAX_RISK_ESCALATION_EVIDENCE = 20
MAX_RISK_ESCALATION_RECORDS = 100


def _ensure_rule(db: Session, *, now: datetime) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == RISK_ESCALATION_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=RISK_ESCALATION_RULE_NAME,
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


def _evidence_for_escalation(db: Session, opportunity_id: int, *, previous_at: datetime | None, current_at: datetime) -> list[dict]:
    conditions = [OpportunityEvidence.opportunity_id == opportunity_id, NormalizedItem.observed_at <= current_at]
    if previous_at is not None:
        conditions.append(NormalizedItem.observed_at > previous_at)
    rows = db.execute(
        select(OpportunityEvidence, NormalizedItem, RawObservation)
        .join(NormalizedItem, NormalizedItem.id == OpportunityEvidence.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(*conditions)
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(MAX_RISK_ESCALATION_EVIDENCE)
    ).all()
    result: list[dict] = []
    seen: set[str] = set()
    for opportunity_evidence, item, raw in rows:
        try:
            evidence_id = evidence_id_for_content_hash(raw.content_hash)
        except (TypeError, ValueError):
            continue
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        result.append({
            "evidence_id": evidence_id,
            "source": item.source_id,
            "type": opportunity_evidence.evidence_type,
            "item_type": item.item_type,
            "quality": raw.evidence_quality,
            "acquisition_method": raw.acquisition_method,
            "provenance": provenance_from_payload(raw.raw_payload).value,
            "title": (item.title or raw.title or "")[:500],
            "text": (item.text or raw.text or "")[:2_000],
            "url": (item.source_url or raw.source_url or "")[:2_000] or None,
            "observed_at": item.observed_at.isoformat(),
        })
    return result


def _change_breakdown(evaluation: RiskEscalationEvaluation, *, current, previous) -> dict:
    return {
        "risk_score_delta": evaluation.absolute_delta,
        "relative_delta": evaluation.relative_delta,
        "evidence_count_delta": current.evidence_count - previous.evidence_count if previous else None,
        "level": {"before": evaluation.previous_level.value if evaluation.previous_level else None, "after": evaluation.current_level.value},
        "stage": {"before": previous.stage if previous else None, "after": current.stage},
        "model_version": {"before": previous.model_version if previous else None, "after": current.model_version},
    }


def _record_kwargs(evaluation: RiskEscalationEvaluation, *, current, previous, evidence: list[dict], delivery_status: str, now: datetime) -> dict:
    return {
        "opportunity_id": evaluation.opportunity_id,
        "input_signature": evaluation.input_signature,
        "contract_version": evaluation.contract_version,
        "algorithm_version": evaluation.algorithm_version,
        "policy": evaluation.policy.model_dump(mode="json"),
        "status": evaluation.status.value,
        "delivery_status": delivery_status,
        "escalated": evaluation.escalated,
        "previous_risk_score": evaluation.previous_risk_score,
        "current_risk_score": evaluation.current_risk_score,
        "absolute_delta": evaluation.absolute_delta,
        "relative_delta": evaluation.relative_delta,
        "previous_level": evaluation.previous_level.value if evaluation.previous_level else None,
        "current_level": evaluation.current_level.value,
        "previous_model_version": evaluation.previous_model_version,
        "current_model_version": evaluation.current_model_version,
        "previous_calculated_at": evaluation.previous_calculated_at,
        "current_calculated_at": evaluation.current_calculated_at,
        "previous_breakdown": previous.breakdown if previous else {},
        "current_breakdown": current.breakdown,
        "change_breakdown": _change_breakdown(evaluation, current=current, previous=previous),
        "evidence_ids": [row["evidence_id"] for row in evidence],
        "evidence": evidence,
        "reasons": list(evaluation.reasons),
        "evaluated_at": evaluation.evaluated_at,
        "created_at": now,
        "updated_at": now,
    }


def _event_key(record: RiskEscalationRecord) -> str:
    return hashlib.sha256(f"risk-escalation-alert-v1:{record.opportunity_id}:{record.input_signature}".encode("utf-8")).hexdigest()


def materialize_risk_escalations(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    policy: RiskEscalationPolicy | None = None,
    evaluated_at: datetime | None = None,
    limit: int = 100,
) -> dict:
    """Persist bounded risk explanations and evidence-backed alert events."""

    if limit < 1 or limit > MAX_RISK_ESCALATION_RECORDS:
        raise ValueError(f"limit must be between 1 and {MAX_RISK_ESCALATION_RECORDS}")
    acquire_alert_evaluation_lock(db)
    result_empty = {"rule": RISK_ESCALATION_RULE_NAME, "evaluated": 0, "escalated": 0, "created": 0, "duplicates": 0, "evidence_missing": 0, "alerts_created": 0, "alert_duplicates": 0, "suppressed": 0}
    if opportunity_ids is not None and not opportunity_ids:
        return result_empty
    policy = policy or RiskEscalationPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    evaluations = detect_risk_escalations(db, opportunity_ids=opportunity_ids, policy=policy, evaluated_at=now, limit=limit)
    result = {**result_empty, "evaluated": len(evaluations), "escalated": sum(1 for item in evaluations if item.escalated)}
    rule = None
    for evaluation in evaluations:
        existing = db.scalar(select(RiskEscalationRecord).where(RiskEscalationRecord.input_signature == evaluation.input_signature))
        if existing is not None:
            result["duplicates"] += 1
            continue
        rows = _snapshots_for_opportunity(db, evaluation.opportunity_id)
        current = _snapshot_input(rows[0])
        previous = _snapshot_input(rows[1]) if len(rows) > 1 else None
        evidence = _evidence_for_escalation(db, evaluation.opportunity_id, previous_at=previous.calculated_at if previous else None, current_at=current.calculated_at)
        if not evaluation.escalated:
            delivery_status = "SUPPRESSED"
            result["suppressed"] += 1
        elif not evidence:
            delivery_status = "REJECTED_NO_EVIDENCE"
            result["evidence_missing"] += 1
        else:
            delivery_status = "READY"
        record = RiskEscalationRecord(**_record_kwargs(evaluation, current=current, previous=previous, evidence=evidence, delivery_status=delivery_status, now=now))
        db.add(record)
        db.flush()
        result["created"] += 1
        if not evaluation.escalated or not evidence:
            continue
        if rule is None:
            rule = _ensure_rule(db, now=now)
        if not rule.enabled:
            record.delivery_status = "SUPPRESSED"
            result["suppressed"] += 1
            continue
        event_key = _event_key(record)
        event = db.scalar(select(AlertEvent).where(AlertEvent.event_key == event_key))
        if event is not None:
            record.alert_event_id = event.id
            record.delivery_status = "DELIVERED"
            result["alert_duplicates"] += 1
            continue
        opportunity = db.get(Opportunity, evaluation.opportunity_id)
        if opportunity is None:
            record.delivery_status = "SUPPRESSED"
            result["suppressed"] += 1
            continue
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=opportunity.id,
            keyword_id=opportunity.keyword_id,
            event_key=event_key,
            status="NEW",
            priority=derive_alert_priority(score=opportunity.score, risk_score=evaluation.current_risk_score, evidence_count=len(record.evidence_ids or [])),
            title=f"Risk escalation: {opportunity.title}"[:300],
            message=(f"Risk escalation for {opportunity.opportunity_key}; previous_risk_score={evaluation.previous_risk_score}; current_risk_score={evaluation.current_risk_score}; "
                     f"absolute_delta={evaluation.absolute_delta}; relative_delta={evaluation.relative_delta}; level={evaluation.previous_level}->{evaluation.current_level}; "
                     f"evidence_ids={','.join(record.evidence_ids or [])}; input_signature={evaluation.input_signature}; alert_event_key={event_key}")[:10_000],
            score=opportunity.score,
            risk_score=evaluation.current_risk_score,
            created_at=evaluation.evaluated_at,
        )
        db.add(event)
        db.flush()
        record.alert_event_id = event.id
        record.delivery_status = "DELIVERED"
        result["alerts_created"] += 1
    if rule is not None:
        rule.last_evaluated_at = now
        rule.updated_at = now
    db.flush()
    return result


def list_risk_escalation_records(db: Session, *, opportunity_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(RiskEscalationRecord).order_by(RiskEscalationRecord.evaluated_at.desc(), RiskEscalationRecord.id.desc()).limit(max(1, min(500, limit)))
    if opportunity_id is not None:
        stmt = stmt.where(RiskEscalationRecord.opportunity_id == opportunity_id)
    if status:
        stmt = stmt.where(RiskEscalationRecord.status == status.strip().upper())
    return [
        {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "input_signature": row.input_signature,
            "contract_version": row.contract_version,
            "algorithm_version": row.algorithm_version,
            "policy": row.policy,
            "status": row.status,
            "delivery_status": row.delivery_status,
            "escalated": row.escalated,
            "previous_risk_score": row.previous_risk_score,
            "current_risk_score": row.current_risk_score,
            "absolute_delta": row.absolute_delta,
            "relative_delta": row.relative_delta,
            "previous_level": row.previous_level,
            "current_level": row.current_level,
            "previous_model_version": row.previous_model_version,
            "current_model_version": row.current_model_version,
            "previous_calculated_at": row.previous_calculated_at,
            "current_calculated_at": row.current_calculated_at,
            "previous_breakdown": row.previous_breakdown or {},
            "current_breakdown": row.current_breakdown or {},
            "change_breakdown": row.change_breakdown or {},
            "evidence_ids": row.evidence_ids or [],
            "evidence": row.evidence or [],
            "reasons": row.reasons or [],
            "alert_event_id": row.alert_event_id,
            "evaluated_at": row.evaluated_at,
        }
        for row in db.scalars(stmt).all()
    ]
