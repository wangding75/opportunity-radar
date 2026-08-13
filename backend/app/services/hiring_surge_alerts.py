"""Persist hiring surge evaluations and create evidence-backed opportunity alerts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, HiringSurgeRecord, Keyword, NormalizedItem, Opportunity, OpportunityKeyword, RawObservation
from app.domain.alert_lifecycle import AlertPriority
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.hiring_surge import HiringSurgeDetection
from app.services.hiring_surge import detect_hiring_surges
from app.services.locks import acquire_alert_evaluation_lock

HIRING_SURGE_RULE_NAME = "HIRING_SURGE"
HIRING_SURGE_MAX_EVIDENCE = 20


def _ensure_hiring_surge_rule(db: Session, *, now: datetime) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == HIRING_SURGE_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=HIRING_SURGE_RULE_NAME,
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


def _evidence(db: Session, detection: HiringSurgeDetection) -> list[dict]:
    content_hashes = [evidence_id[4:] for evidence_id in detection.evidence_ids if evidence_id.startswith("ev1_")]
    if not content_hashes:
        return []
    rows = db.execute(
        select(NormalizedItem, RawObservation)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(
            NormalizedItem.item_type == "JOB",
            RawObservation.content_hash.in_(content_hashes),
        )
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(HIRING_SURGE_MAX_EVIDENCE)
    ).all()
    result: list[dict] = []
    seen: set[str] = set()
    for item, raw in rows:
        evidence_id = evidence_id_for_content_hash(raw.content_hash)
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        result.append({
            "evidence_id": evidence_id,
            "source": item.source_id,
            "type": "HIRING",
            "item_type": item.item_type,
            "quality": raw.evidence_quality,
            "acquisition_method": raw.acquisition_method,
            "provenance": provenance_from_payload(raw.raw_payload).value,
            "title": (item.title or "")[:500],
            "text": (item.text or "")[:2_000],
            "url": (item.source_url or "")[:2_000] or None,
            "observed_at": item.observed_at.isoformat(),
        })
    return result


def _opportunity_for_keyword(db: Session, keyword_id: int) -> Opportunity | None:
    return db.scalar(
        select(Opportunity)
        .join(OpportunityKeyword, OpportunityKeyword.opportunity_id == Opportunity.id)
        .where(OpportunityKeyword.keyword_id == keyword_id, Opportunity.stage != "DORMANT")
        .order_by(Opportunity.score.desc(), Opportunity.id.asc())
    )


def _record_kwargs(detection: HiringSurgeDetection, *, status: str, opportunity_id: int | None, evidence: list[dict], explanation: dict, alert_event_id: int | None) -> dict:
    evaluation = detection.evaluation
    return {
        "keyword_id": evaluation.keyword_id,
        "opportunity_id": opportunity_id,
        "detection_signature": detection.detection_signature,
        "input_signature": evaluation.input_signature,
        "contract_version": evaluation.contract_version,
        "algorithm_version": evaluation.algorithm_version,
        "policy": evaluation.policy.model_dump(mode="json"),
        "current_start": evaluation.current_start,
        "current_end": evaluation.current_end,
        "baseline_start": evaluation.baseline_start,
        "baseline_end": evaluation.baseline_end,
        "status": status,
        "comparison": evaluation.comparison.value,
        "surge": evaluation.surge,
        "current_jobs": evaluation.current_jobs,
        "baseline_jobs": evaluation.baseline_jobs,
        "current_sources": evaluation.current_sources,
        "baseline_sources": evaluation.baseline_sources,
        "current_evidence": evaluation.current_evidence,
        "baseline_evidence": evaluation.baseline_evidence,
        "growth_rate": evaluation.growth_rate,
        "absolute_delta": evaluation.absolute_delta,
        "z_score": evaluation.z_score,
        "evidence_ids": list(detection.evidence_ids),
        "evidence": evidence,
        "metrics": detection.metrics.model_dump(mode="json"),
        "explanation": explanation,
        "alert_event_id": alert_event_id,
        "evaluated_at": evaluation.evaluated_at,
        "created_at": evaluation.evaluated_at,
        "updated_at": evaluation.evaluated_at,
    }


def materialize_hiring_surge_alerts(
    db: Session,
    *,
    keyword_ids: set[int] | None = None,
    window_end=None,
    limit: int = 100,
) -> dict:
    """Persist all bounded evaluations and alert only evidence-backed surges."""

    acquire_alert_evaluation_lock(db)
    now = utc_now()
    detections = detect_hiring_surges(db, keyword_ids=keyword_ids, window_end=window_end, anomalous_only=False, limit=limit)
    result = {"rule": HIRING_SURGE_RULE_NAME, "evaluated": len(detections), "surges": 0, "created": 0, "duplicates": 0, "evidence_missing": 0, "opportunities_linked": 0}
    if not detections:
        return result
    rule = _ensure_hiring_surge_rule(db, now=now)
    for detection in detections:
        existing = db.scalar(select(HiringSurgeRecord).where(HiringSurgeRecord.detection_signature == detection.detection_signature))
        if existing is not None:
            result["duplicates"] += 1
            continue
        evaluation = detection.evaluation
        opportunity = _opportunity_for_keyword(db, evaluation.keyword_id)
        opportunity_id = opportunity.id if opportunity is not None else None
        if opportunity_id is not None:
            result["opportunities_linked"] += 1
        evidence = _evidence(db, detection) if evaluation.surge else []
        status = "STABLE"
        alert_event_id = None
        explanation = {
            "contract_version": evaluation.contract_version,
            "algorithm_version": evaluation.algorithm_version,
            "policy_version": evaluation.policy.policy_version,
            "evaluation": evaluation.model_dump(mode="json"),
            "metrics": detection.metrics.model_dump(mode="json"),
            "detection_signature": detection.detection_signature,
            "evidence_ids": [row["evidence_id"] for row in evidence],
            "opportunity_id": opportunity_id,
        }
        if evaluation.surge:
            result["surges"] += 1
            if not evidence:
                status = "REJECTED_NO_EVIDENCE"
                result["evidence_missing"] += 1
                explanation["fail_closed_reason"] = "surge has no resolvable raw job evidence"
            else:
                status = "SURGE"
                keyword = db.get(Keyword, evaluation.keyword_id)
                event = AlertEvent(
                    alert_rule_id=rule.id,
                    opportunity_id=opportunity_id,
                    keyword_id=evaluation.keyword_id,
                    event_key=detection.detection_signature,
                    status="NEW",
                    priority=AlertPriority.HIGH.value,
                    title=f"Hiring surge: {keyword.display_name if keyword else evaluation.keyword}",
                    message=(
                        f"Hiring surge for {evaluation.keyword}; current_jobs={evaluation.current_jobs}; "
                        f"baseline_jobs={evaluation.baseline_jobs}; growth_rate={evaluation.growth_rate}; "
                        f"delta={evaluation.absolute_delta}; z_score={evaluation.z_score}; "
                        f"opportunity_id={opportunity_id}; evidence_ids={','.join(row['evidence_id'] for row in evidence)}; "
                        f"detection_signature={detection.detection_signature}"
                    )[:10_000],
                    score=min(100.0, max(0.0, (evaluation.growth_rate or 1.0) * 100.0)),
                    risk_score=0.0,
                    created_at=evaluation.evaluated_at,
                )
                db.add(event)
                db.flush()
                alert_event_id = event.id
                result["created"] += 1
                explanation["alert_event_id"] = event.id
        db.add(HiringSurgeRecord(**_record_kwargs(detection, status=status, opportunity_id=opportunity_id, evidence=evidence, explanation=explanation, alert_event_id=alert_event_id)))
    rule.last_evaluated_at = now
    rule.updated_at = now
    db.flush()
    return result


def list_hiring_surge_records(db: Session, *, keyword_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(HiringSurgeRecord).order_by(HiringSurgeRecord.evaluated_at.desc(), HiringSurgeRecord.id.desc()).limit(max(1, min(500, limit)))
    if keyword_id is not None:
        stmt = stmt.where(HiringSurgeRecord.keyword_id == keyword_id)
    if status:
        stmt = stmt.where(HiringSurgeRecord.status == status.strip().upper())
    return [
        {
            "id": row.id,
            "keyword_id": row.keyword_id,
            "opportunity_id": row.opportunity_id,
            "detection_signature": row.detection_signature,
            "input_signature": row.input_signature,
            "contract_version": row.contract_version,
            "algorithm_version": row.algorithm_version,
            "policy": row.policy,
            "current_start": row.current_start,
            "current_end": row.current_end,
            "baseline_start": row.baseline_start,
            "baseline_end": row.baseline_end,
            "status": row.status,
            "comparison": row.comparison,
            "surge": row.surge,
            "current_jobs": row.current_jobs,
            "baseline_jobs": row.baseline_jobs,
            "current_sources": row.current_sources,
            "baseline_sources": row.baseline_sources,
            "current_evidence": row.current_evidence,
            "baseline_evidence": row.baseline_evidence,
            "growth_rate": row.growth_rate,
            "absolute_delta": row.absolute_delta,
            "z_score": row.z_score,
            "evidence_ids": row.evidence_ids or [],
            "evidence": row.evidence or [],
            "metrics": row.metrics or {},
            "explanation": row.explanation or {},
            "alert_event_id": row.alert_event_id,
            "evaluated_at": row.evaluated_at,
        }
        for row in db.scalars(stmt).all()
    ]
