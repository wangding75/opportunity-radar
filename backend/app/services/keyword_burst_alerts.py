"""Persist keyword burst explanations and materialize evidence-backed alerts."""

from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, KeywordBurstRecord, KeywordMention, NormalizedItem, RawObservation
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.keyword_burst import KeywordBurstEvaluation, KeywordBurstPolicy
from app.services.keyword_burst import detect_keyword_bursts
from app.services.locks import acquire_alert_evaluation_lock

KEYWORD_BURST_RULE_NAME = "KEYWORD_BURST"
MAX_BURST_EVIDENCE = 20


def _ensure_keyword_burst_rule(db: Session, *, now: datetime) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == KEYWORD_BURST_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=KEYWORD_BURST_RULE_NAME,
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


def _burst_evidence(db: Session, evaluation: KeywordBurstEvaluation) -> list[dict]:
    start_at = datetime.combine(evaluation.baseline_start, time.min)
    end_at = datetime.combine(evaluation.current_end, time.min)
    rows = db.execute(
        select(NormalizedItem, RawObservation)
        .join(KeywordMention, KeywordMention.normalized_item_id == NormalizedItem.id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(
            KeywordMention.keyword_id == evaluation.keyword_id,
            KeywordMention.observed_at >= start_at,
            KeywordMention.observed_at < end_at,
        )
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(MAX_BURST_EVIDENCE)
    ).all()
    evidence: list[dict] = []
    seen: set[str] = set()
    for item, raw in rows:
        evidence_id = evidence_id_for_content_hash(raw.content_hash)
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        evidence.append({
            "evidence_id": evidence_id,
            "source": item.source_id,
            "type": item.item_type,
            "item_type": item.item_type,
            "quality": raw.evidence_quality,
            "acquisition_method": raw.acquisition_method,
            "provenance": provenance_from_payload(raw.raw_payload).value,
            "title": (item.title or "")[:500],
            "text": (item.text or "")[:2_000],
            "url": (item.source_url or "")[:2_000] or None,
            "observed_at": item.observed_at.isoformat(),
        })
    return evidence


def _explanation(evaluation: KeywordBurstEvaluation, evidence: list[dict]) -> dict:
    explanation = {
        "contract_version": evaluation.contract_version,
        "algorithm_version": evaluation.algorithm_version,
        "policy_version": evaluation.policy.policy_version,
        "window": {
            "current_start": evaluation.current_start.isoformat(),
            "current_end": evaluation.current_end.isoformat(),
            "baseline_start": evaluation.baseline_start.isoformat(),
            "baseline_end": evaluation.baseline_end.isoformat(),
        },
        "comparison": evaluation.comparison.value,
        "current_observations": evaluation.current_observations,
        "baseline_observations": evaluation.baseline_observations,
        "absolute_delta": evaluation.absolute_delta,
        "growth_rate": evaluation.growth_rate,
        "z_score": evaluation.z_score,
        "baseline_mean_daily": evaluation.baseline_mean_daily,
        "baseline_stddev_daily": evaluation.baseline_stddev_daily,
        "current_mean_daily": evaluation.current_mean_daily,
        "current_sources": evaluation.current_sources,
        "reasons": list(evaluation.reasons),
        "input_signature": evaluation.input_signature,
        "evidence_ids": [row["evidence_id"] for row in evidence],
    }
    if evaluation.anomalous and not evidence:
        explanation["fail_closed_reason"] = "anomaly has no resolvable raw evidence"
    return explanation


def _record_kwargs(evaluation: KeywordBurstEvaluation, *, status: str, evidence: list[dict], explanation: dict, alert_event_id: int | None) -> dict:
    return {
        "keyword_id": evaluation.keyword_id,
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
        "current_observations": evaluation.current_observations,
        "baseline_observations": evaluation.baseline_observations,
        "current_sources": evaluation.current_sources,
        "baseline_sources": evaluation.baseline_sources,
        "baseline_mean_daily": evaluation.baseline_mean_daily,
        "baseline_stddev_daily": evaluation.baseline_stddev_daily,
        "current_mean_daily": evaluation.current_mean_daily,
        "growth_rate": evaluation.growth_rate,
        "absolute_delta": evaluation.absolute_delta,
        "z_score": evaluation.z_score,
        "reasons": list(evaluation.reasons),
        "evidence": evidence,
        "explanation": explanation,
        "alert_event_id": alert_event_id,
        "evaluated_at": evaluation.evaluated_at,
        "created_at": evaluation.evaluated_at,
        "updated_at": evaluation.evaluated_at,
    }


def materialize_keyword_burst_alerts(
    db: Session,
    *,
    keyword_ids: set[int] | None = None,
    window_end=None,
    policy: KeywordBurstPolicy | None = None,
    limit: int = 100,
) -> dict:
    """Persist evaluations and create idempotent, evidence-backed alert events."""

    acquire_alert_evaluation_lock(db)
    now = utc_now()
    evaluations = detect_keyword_bursts(db, keyword_ids=keyword_ids, window_end=window_end, policy=policy, limit=limit)
    if not evaluations:
        return {"rule": KEYWORD_BURST_RULE_NAME, "evaluated": 0, "anomalous": 0, "created": 0, "duplicates": 0, "evidence_missing": 0}
    rule = _ensure_keyword_burst_rule(db, now=now)
    anomalous = 0
    created = 0
    duplicates = 0
    evidence_missing = 0
    for evaluation in evaluations:
        existing = db.scalar(select(KeywordBurstRecord).where(KeywordBurstRecord.input_signature == evaluation.input_signature))
        if existing is not None:
            duplicates += 1
            continue
        evidence = _burst_evidence(db, evaluation) if evaluation.anomalous else []
        explanation = _explanation(evaluation, evidence)
        if not evaluation.anomalous:
            db.add(KeywordBurstRecord(**_record_kwargs(evaluation, status="STABLE", evidence=evidence, explanation=explanation, alert_event_id=None)))
            continue
        anomalous += 1
        if not evidence:
            evidence_missing += 1
            db.add(KeywordBurstRecord(**_record_kwargs(evaluation, status="REJECTED_NO_EVIDENCE", evidence=evidence, explanation=explanation, alert_event_id=None)))
            continue
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=None,
            keyword_id=evaluation.keyword_id,
            event_key=evaluation.input_signature,
            status="NEW",
            priority=5,
            title=f"Keyword burst: {evaluation.keyword}",
            message=(f"Keyword {evaluation.keyword} burst from {evaluation.baseline_mean_daily:.2f} to {evaluation.current_mean_daily:.2f} daily observations; "
                     f"delta={evaluation.absolute_delta}, growth={evaluation.growth_rate}, z_score={evaluation.z_score}. "
                     f"evidence_ids={','.join(row['evidence_id'] for row in evidence)}; input_signature={evaluation.input_signature}")[:10_000],
            score=min(100.0, evaluation.z_score * 20),
            risk_score=0.0,
            created_at=evaluation.evaluated_at,
        )
        db.add(event)
        db.flush()
        db.add(KeywordBurstRecord(**_record_kwargs(evaluation, status="ANOMALOUS", evidence=evidence, explanation=explanation, alert_event_id=event.id)))
        created += 1
    rule.last_evaluated_at = now
    rule.updated_at = now
    db.flush()
    return {"rule": KEYWORD_BURST_RULE_NAME, "evaluated": len(evaluations), "anomalous": anomalous, "created": created, "duplicates": duplicates, "evidence_missing": evidence_missing}


def list_keyword_burst_records(db: Session, *, keyword_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(KeywordBurstRecord).order_by(KeywordBurstRecord.evaluated_at.desc(), KeywordBurstRecord.id.desc()).limit(max(1, min(500, limit)))
    if keyword_id is not None:
        stmt = stmt.where(KeywordBurstRecord.keyword_id == keyword_id)
    if status:
        stmt = stmt.where(KeywordBurstRecord.status == status.strip().upper())
    return [
        {
            "id": row.id,
            "keyword_id": row.keyword_id,
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
            "current_observations": row.current_observations,
            "baseline_observations": row.baseline_observations,
            "current_sources": row.current_sources,
            "baseline_sources": row.baseline_sources,
            "growth_rate": row.growth_rate,
            "absolute_delta": row.absolute_delta,
            "z_score": row.z_score,
            "reasons": row.reasons or [],
            "evidence": row.evidence or [],
            "explanation": row.explanation or {},
            "alert_event_id": row.alert_event_id,
            "evaluated_at": row.evaluated_at,
        }
        for row in db.scalars(stmt).all()
    ]
