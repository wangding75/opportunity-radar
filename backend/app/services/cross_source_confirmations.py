"""Materialize source-independent evidence confirmation records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import CrossSourceConfirmationRecord, NormalizedItem, Opportunity, OpportunityEvidence, RawObservation
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.cross_source_confirmation import (
    CrossSourceConfirmationEvaluation,
    CrossSourceConfirmationInput,
    CrossSourceConfirmationPolicy,
    CrossSourceEvidence,
    claim_fingerprint,
    evaluate_cross_source_confirmation,
    source_endpoint_key,
)
from app.services.locks import acquire_derived_analysis_lock

CROSS_SOURCE_CONFIRMATION_RULE_NAME = "CROSS_SOURCE_CONFIRMATION"
MAX_CONFIRMATION_OPPORTUNITIES = 100
MAX_CONFIRMATION_ROWS = 10_000


def _evidence_for_opportunity(db: Session, opportunity_id: int, *, limit: int) -> list[CrossSourceEvidence]:
    rows = db.execute(
        select(NormalizedItem, RawObservation)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .join(OpportunityEvidence, OpportunityEvidence.normalized_item_id == NormalizedItem.id)
        .where(OpportunityEvidence.opportunity_id == opportunity_id)
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(limit)
    ).all()
    evidence: list[CrossSourceEvidence] = []
    for item, raw in rows:
        try:
            evidence.append(
                CrossSourceEvidence(
                    evidence_id=evidence_id_for_content_hash(raw.content_hash),
                    source_id=item.source_id,
                    title=item.title or raw.title or "",
                    text=item.text or raw.text or "",
                    url=item.source_url or raw.source_url,
                    observed_at=item.observed_at,
                    provenance=provenance_from_payload(raw.raw_payload),
                )
            )
        except (TypeError, ValueError):
            # Invalid or unresolvable evidence never becomes a positive signal.
            continue
    return evidence


def _citation_rows(evaluation: CrossSourceConfirmationEvaluation, evidence: list[CrossSourceEvidence]) -> list[dict]:
    by_id = {row.evidence_id: row for row in evidence}
    return [
        {
            "evidence_id": row.evidence_id,
            "source_id": row.source_id,
            "endpoint": source_endpoint_key(row.source_id, row.url),
            "claim_fingerprint": claim_fingerprint(row),
            "provenance": row.provenance.value,
            "title": row.title[:500],
            "text": row.text[:2_000],
            "url": row.url,
            "observed_at": row.observed_at.isoformat(),
        }
        for evidence_id in evaluation.evidence_ids
        if (row := by_id.get(evidence_id)) is not None
    ]


def _record_kwargs(
    opportunity: Opportunity,
    evaluation: CrossSourceConfirmationEvaluation,
    *,
    evidence: list[CrossSourceEvidence],
    now: datetime,
) -> dict:
    return {
        "opportunity_id": opportunity.id,
        "subject_key": evaluation.subject_key,
        "input_signature": evaluation.input_signature,
        "contract_version": evaluation.contract_version,
        "algorithm_version": evaluation.algorithm_version,
        "policy": evaluation.policy.model_dump(mode="json"),
        "status": evaluation.status.value,
        "confirmed": evaluation.confirmed,
        "input_evidence_count": evaluation.input_evidence_count,
        "fresh_evidence_count": evaluation.fresh_evidence_count,
        "deduplicated_evidence_count": evaluation.deduplicated_evidence_count,
        "stale_evidence_count": evaluation.stale_evidence_count,
        "future_evidence_count": evaluation.future_evidence_count,
        "independent_source_count": evaluation.independent_source_count,
        "unique_claim_count": evaluation.unique_claim_count,
        "source_endpoints": list(evaluation.source_endpoints),
        "evidence_ids": list(evaluation.evidence_ids),
        "claim_fingerprints": list(evaluation.claim_fingerprints),
        "evidence": _citation_rows(evaluation, evidence),
        "reasons": list(evaluation.reasons),
        "evaluated_at": evaluation.evaluated_at,
        "created_at": now,
        "updated_at": now,
    }


def materialize_cross_source_confirmations(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    evaluated_at: datetime | None = None,
    policy: CrossSourceConfirmationPolicy | None = None,
    limit: int = 100,
) -> dict:
    """Persist bounded source-independence decisions without creating alerts."""

    if limit < 1 or limit > MAX_CONFIRMATION_OPPORTUNITIES:
        raise ValueError(f"limit must be between 1 and {MAX_CONFIRMATION_OPPORTUNITIES}")
    acquire_derived_analysis_lock(db)
    policy = policy or CrossSourceConfirmationPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    if opportunity_ids is not None and not opportunity_ids:
        return {"rule": CROSS_SOURCE_CONFIRMATION_RULE_NAME, "evaluated": 0, "confirmed": 0, "created": 0, "duplicates": 0, "no_evidence": 0, "insufficient": 0}
    stmt = select(Opportunity).where(Opportunity.stage != "DORMANT").order_by(Opportunity.id).limit(limit)
    if opportunity_ids is not None:
        stmt = stmt.where(Opportunity.id.in_(opportunity_ids))
    opportunities = db.scalars(stmt).all()
    result = {"rule": CROSS_SOURCE_CONFIRMATION_RULE_NAME, "evaluated": len(opportunities), "confirmed": 0, "created": 0, "duplicates": 0, "no_evidence": 0, "insufficient": 0}
    for opportunity in opportunities:
        evidence = _evidence_for_opportunity(db, opportunity.id, limit=min(policy.max_evidence, MAX_CONFIRMATION_ROWS))
        evaluation = evaluate_cross_source_confirmation(
            CrossSourceConfirmationInput(subject_key=opportunity.opportunity_key, evidence=evidence),
            policy=policy,
            evaluated_at=now,
        )
        if evaluation.confirmed:
            result["confirmed"] += 1
        if evaluation.status.value == "NO_EVIDENCE":
            result["no_evidence"] += 1
        elif evaluation.status.value == "INSUFFICIENT_EVIDENCE":
            result["insufficient"] += 1
        if db.scalar(select(CrossSourceConfirmationRecord.id).where(CrossSourceConfirmationRecord.input_signature == evaluation.input_signature)) is not None:
            result["duplicates"] += 1
            continue
        db.add(CrossSourceConfirmationRecord(**_record_kwargs(opportunity, evaluation, evidence=evidence, now=now)))
        result["created"] += 1
    db.flush()
    return result


def list_cross_source_confirmations(
    db: Session,
    *,
    opportunity_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = select(CrossSourceConfirmationRecord).order_by(CrossSourceConfirmationRecord.evaluated_at.desc(), CrossSourceConfirmationRecord.id.desc()).limit(max(1, min(500, limit)))
    if opportunity_id is not None:
        stmt = stmt.where(CrossSourceConfirmationRecord.opportunity_id == opportunity_id)
    if status:
        stmt = stmt.where(CrossSourceConfirmationRecord.status == status.strip().upper())
    return [
        {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "subject_key": row.subject_key,
            "input_signature": row.input_signature,
            "contract_version": row.contract_version,
            "algorithm_version": row.algorithm_version,
            "policy": row.policy,
            "status": row.status,
            "confirmed": row.confirmed,
            "input_evidence_count": row.input_evidence_count,
            "fresh_evidence_count": row.fresh_evidence_count,
            "deduplicated_evidence_count": row.deduplicated_evidence_count,
            "stale_evidence_count": row.stale_evidence_count,
            "future_evidence_count": row.future_evidence_count,
            "independent_source_count": row.independent_source_count,
            "unique_claim_count": row.unique_claim_count,
            "source_endpoints": row.source_endpoints or [],
            "evidence_ids": row.evidence_ids or [],
            "claim_fingerprints": row.claim_fingerprints or [],
            "evidence": row.evidence or [],
            "reasons": row.reasons or [],
            "score_contract_version": row.score_contract_version,
            "score_algorithm_version": row.score_algorithm_version,
            "score_input_signature": row.score_input_signature,
            "score": row.score,
            "risk_score": row.risk_score,
            "score_breakdown": row.score_breakdown or {},
            "alert_event_id": row.alert_event_id,
            "evaluated_at": row.evaluated_at,
        }
        for row in db.scalars(stmt).all()
    ]
