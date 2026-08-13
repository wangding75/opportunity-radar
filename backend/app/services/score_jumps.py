"""Detect and persist bounded score jump evaluations from score snapshots."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import NormalizedItem, Opportunity, OpportunityEvidence, OpportunityScoreSnapshot, RawObservation, ScoreJumpRecord
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.score_jump import ScoreJumpInput, ScoreJumpPolicy, ScoreSnapshotInput, evaluate_score_jump
from app.services.locks import acquire_alert_evaluation_lock

SCORE_JUMP_RULE_NAME = "SCORE_JUMP"
MAX_SCORE_JUMP_OPPORTUNITIES = 100
MAX_SCORE_JUMP_SNAPSHOTS = 2


def _snapshot_input(row: OpportunityScoreSnapshot) -> ScoreSnapshotInput:
    return ScoreSnapshotInput(
        opportunity_id=row.opportunity_id,
        model_version=row.model_version,
        input_signature=row.input_signature,
        score=row.score,
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
        .limit(MAX_SCORE_JUMP_SNAPSHOTS)
    ).all()


def _evidence_for_jump(
    db: Session,
    opportunity_id: int,
    *,
    previous_at: datetime | None,
    current_at: datetime,
    limit: int = 20,
) -> list[dict]:
    """Return only opportunity evidence observed in the compared snapshot window."""

    conditions = [
        OpportunityEvidence.opportunity_id == opportunity_id,
        NormalizedItem.observed_at <= current_at,
    ]
    if previous_at is not None:
        conditions.append(NormalizedItem.observed_at > previous_at)
    rows = db.execute(
        select(OpportunityEvidence, NormalizedItem, RawObservation)
        .join(NormalizedItem, NormalizedItem.id == OpportunityEvidence.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(*conditions)
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(limit)
    ).all()
    evidence: list[dict] = []
    seen: set[str] = set()
    for opportunity_evidence, item, raw in rows:
        try:
            evidence_id = evidence_id_for_content_hash(raw.content_hash)
        except (TypeError, ValueError):
            # Invalid ingestion identities cannot be cited or bound to a jump.
            continue
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        evidence.append(
            {
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
            }
        )
    return evidence


def _change_breakdown(current: ScoreSnapshotInput, previous: ScoreSnapshotInput | None, evaluation) -> dict:
    return {
        "score_delta": evaluation.absolute_delta,
        "relative_delta": evaluation.relative_delta,
        "risk_score_delta": round(current.risk_score - previous.risk_score, 6) if previous else None,
        "evidence_count_delta": current.evidence_count - previous.evidence_count if previous else None,
        "stage": {"before": previous.stage if previous else None, "after": current.stage},
        "model_version": {"before": previous.model_version if previous else None, "after": current.model_version},
    }


def _record_kwargs(
    evaluation,
    *,
    current: ScoreSnapshotInput,
    previous: ScoreSnapshotInput | None,
    evidence: list[dict],
    now: datetime,
) -> dict:
    return {
        "opportunity_id": evaluation.opportunity_id,
        "input_signature": evaluation.input_signature,
        "contract_version": evaluation.contract_version,
        "algorithm_version": evaluation.algorithm_version,
        "policy": evaluation.policy.model_dump(mode="json"),
        "status": evaluation.status.value,
        "jumped": evaluation.jumped,
        "previous_snapshot_signature": previous.input_signature if previous else None,
        "current_snapshot_signature": current.input_signature,
        "previous_model_version": evaluation.previous_model_version,
        "current_model_version": evaluation.current_model_version,
        "previous_score": evaluation.previous_score,
        "current_score": evaluation.current_score,
        "absolute_delta": evaluation.absolute_delta,
        "relative_delta": evaluation.relative_delta,
        "previous_calculated_at": evaluation.previous_calculated_at,
        "current_calculated_at": evaluation.current_calculated_at,
        "previous_breakdown": previous.breakdown if previous else {},
        "current_breakdown": current.breakdown,
        "change_breakdown": _change_breakdown(current, previous, evaluation),
        "evidence_ids": [row["evidence_id"] for row in evidence],
        "evidence": evidence,
        "reasons": list(evaluation.reasons),
        "evaluated_at": evaluation.evaluated_at,
        "created_at": now,
        "updated_at": now,
    }


def materialize_score_jumps(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    evaluated_at: datetime | None = None,
    policy: ScoreJumpPolicy | None = None,
    limit: int = 100,
) -> dict:
    """Persist one comparison for each bounded opportunity with score history."""

    if limit < 1 or limit > MAX_SCORE_JUMP_OPPORTUNITIES:
        raise ValueError(f"limit must be between 1 and {MAX_SCORE_JUMP_OPPORTUNITIES}")
    acquire_alert_evaluation_lock(db)
    policy = policy or ScoreJumpPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    if opportunity_ids is not None and not opportunity_ids:
        return {"rule": SCORE_JUMP_RULE_NAME, "evaluated": 0, "jumped": 0, "created": 0, "duplicates": 0, "no_baseline": 0, "suppressed": 0}
    stmt = select(Opportunity.id).where(Opportunity.stage != "DORMANT").order_by(Opportunity.id).limit(limit)
    if opportunity_ids is not None:
        stmt = stmt.where(Opportunity.id.in_(opportunity_ids))
    selected_ids = list(db.scalars(stmt).all())
    result = {"rule": SCORE_JUMP_RULE_NAME, "evaluated": 0, "jumped": 0, "created": 0, "duplicates": 0, "no_baseline": 0, "suppressed": 0}
    for opportunity_id in selected_ids:
        rows = _snapshots_for_opportunity(db, opportunity_id)
        if not rows:
            continue
        current = _snapshot_input(rows[0])
        previous = _snapshot_input(rows[1]) if len(rows) > 1 else None
        evaluation = evaluate_score_jump(
            ScoreJumpInput(opportunity_id=opportunity_id, previous=previous, current=current),
            policy=policy,
            evaluated_at=now,
        )
        evidence = _evidence_for_jump(
            db,
            opportunity_id,
            previous_at=previous.calculated_at if previous else None,
            current_at=current.calculated_at,
        )
        result["evaluated"] += 1
        if evaluation.jumped:
            result["jumped"] += 1
        if evaluation.status.value == "NO_BASELINE":
            result["no_baseline"] += 1
        elif not evaluation.jumped:
            result["suppressed"] += 1
        if db.scalar(select(ScoreJumpRecord.id).where(ScoreJumpRecord.input_signature == evaluation.input_signature)) is not None:
            result["duplicates"] += 1
            continue
        db.add(ScoreJumpRecord(**_record_kwargs(evaluation, current=current, previous=previous, evidence=evidence, now=now)))
        result["created"] += 1
    db.flush()
    return result


def list_score_jump_records(db: Session, *, opportunity_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(ScoreJumpRecord).order_by(ScoreJumpRecord.evaluated_at.desc(), ScoreJumpRecord.id.desc()).limit(max(1, min(500, limit)))
    if opportunity_id is not None:
        stmt = stmt.where(ScoreJumpRecord.opportunity_id == opportunity_id)
    if status:
        stmt = stmt.where(ScoreJumpRecord.status == status.strip().upper())
    return [
        {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "input_signature": row.input_signature,
            "contract_version": row.contract_version,
            "algorithm_version": row.algorithm_version,
            "policy": row.policy,
            "status": row.status,
            "jumped": row.jumped,
            "previous_snapshot_signature": row.previous_snapshot_signature,
            "current_snapshot_signature": row.current_snapshot_signature,
            "previous_model_version": row.previous_model_version,
            "current_model_version": row.current_model_version,
            "previous_score": row.previous_score,
            "current_score": row.current_score,
            "absolute_delta": row.absolute_delta,
            "relative_delta": row.relative_delta,
            "previous_calculated_at": row.previous_calculated_at,
            "current_calculated_at": row.current_calculated_at,
            "previous_breakdown": row.previous_breakdown or {},
            "current_breakdown": row.current_breakdown or {},
            "change_breakdown": row.change_breakdown or {},
            "evidence_ids": row.evidence_ids or [],
            "evidence": row.evidence or [],
            "reasons": row.reasons or [],
            "evaluated_at": row.evaluated_at,
        }
        for row in db.scalars(stmt).all()
    ]
