"""Daily opportunity digest generation over persisted opportunity state."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import NormalizedItem, Opportunity, OpportunityEvidence, RawObservation
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.digest import (
    DIGEST_ALGORITHM_VERSION,
    DIGEST_CONTRACT_VERSION,
    DIGEST_MAX_CANDIDATES,
    DigestEvidenceProvenance,
    DigestItem,
    DigestSelectionPolicy,
    DigestStatus,
    DailyDigest,
    build_digest_input_signature,
)


def _ranking_key(item: DigestItem) -> tuple[float, float, timedelta, str, int]:
    return (-item.score, item.risk_score, datetime.max - item.last_seen_at, item.opportunity_key, item.opportunity_id)


def deduplicate_and_rank_digest_items(
    items: Iterable[DigestItem],
    *,
    policy: DigestSelectionPolicy,
) -> list[DigestItem]:
    """Deduplicate by stable opportunity key and apply the documented ordering."""

    selected_by_key: dict[str, DigestItem] = {}
    for item in items:
        current = selected_by_key.get(item.opportunity_key)
        if current is None or _ranking_key(item) < _ranking_key(current):
            selected_by_key[item.opportunity_key] = item
    ranked = sorted(selected_by_key.values(), key=_ranking_key)[: policy.max_items]
    return [item.model_copy(update={"rank": rank}) for rank, item in enumerate(ranked, start=1)]


def _fallback_analysis_signature(opportunity: Opportunity) -> str:
    if opportunity.analysis_signature and len(opportunity.analysis_signature) == 64:
        try:
            int(opportunity.analysis_signature, 16)
            return opportunity.analysis_signature.lower()
        except ValueError:
            # Invalid legacy signatures fall through to the deterministic
            # database-backed signature below instead of being treated as valid.
            invalid_signature = opportunity.analysis_signature
    payload = {
        "opportunity_id": opportunity.id,
        "opportunity_key": opportunity.opportunity_key,
        "score": opportunity.score,
        "risk_score": opportunity.risk_score,
        "evidence_count": opportunity.evidence_count,
        "updated_at": str(opportunity.updated_at),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _evidence_context(db: Session, opportunity_ids: set[int]) -> dict[int, tuple[list[str], DigestEvidenceProvenance]]:
    if not opportunity_ids:
        return {}
    rows = db.execute(
        select(OpportunityEvidence.opportunity_id, RawObservation.content_hash, RawObservation.raw_payload)
        .join(NormalizedItem, NormalizedItem.id == OpportunityEvidence.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(OpportunityEvidence.opportunity_id.in_(opportunity_ids))
        .order_by(OpportunityEvidence.opportunity_id, OpportunityEvidence.observed_at.desc(), OpportunityEvidence.id.desc())
    ).all()
    by_opportunity: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for opportunity_id, content_hash, raw_payload in rows:
        provenance = provenance_from_payload(raw_payload).value
        evidence_id = evidence_id_for_content_hash(content_hash)
        if all(existing_id != evidence_id for existing_id, _ in by_opportunity[opportunity_id]):
            by_opportunity[opportunity_id].append((evidence_id, provenance))

    result: dict[int, tuple[list[str], DigestEvidenceProvenance]] = {}
    for opportunity_id, values in by_opportunity.items():
        evidence_ids = [evidence_id for evidence_id, _ in values]
        provenances = {provenance for _, provenance in values}
        provenance = next(iter(provenances)) if len(provenances) == 1 else DigestEvidenceProvenance.MIXED.value
        result[opportunity_id] = (evidence_ids, DigestEvidenceProvenance(provenance))
    return result


def _digest_item(opportunity: Opportunity, *, evidence_ids: list[str], provenance: DigestEvidenceProvenance) -> DigestItem:
    return DigestItem(
        rank=1,
        opportunity_id=opportunity.id,
        opportunity_key=opportunity.opportunity_key,
        title=opportunity.title,
        stage=opportunity.stage,
        score=opportunity.score,
        risk_score=opportunity.risk_score,
        evidence_count=opportunity.evidence_count,
        summary=opportunity.summary or "",
        analysis_status=opportunity.analysis_status,
        analysis_provider=opportunity.analysis_provider,
        analysis_signature=_fallback_analysis_signature(opportunity),
        last_seen_at=opportunity.last_seen_at,
        evidence_ids=evidence_ids,
        evidence_provenance=provenance,
        selection_reasons=[
            f"score >= {opportunity.score:g}",
            "non-dormant opportunity",
            f"evidence_count = {opportunity.evidence_count}",
        ],
        score_breakdown=opportunity.score_breakdown or {},
    )


def generate_daily_digest(
    db: Session,
    *,
    digest_date: date | None = None,
    now: datetime | None = None,
    policy: DigestSelectionPolicy | None = None,
) -> DailyDigest:
    """Generate one bounded UTC daily snapshot without changing source state."""

    policy = policy or DigestSelectionPolicy()
    now = now or utc_now()
    day = digest_date or now.date()
    window_start = datetime.combine(day, time.min)
    window_end = window_start + timedelta(days=1)
    filters = [
        Opportunity.stage != "DORMANT" if policy.exclude_dormant else True,
        Opportunity.score >= policy.min_score,
        Opportunity.evidence_count >= policy.min_evidence_count,
    ]
    total = int(db.scalar(select(func.count()).select_from(Opportunity).where(*filters)) or 0)
    rows = db.scalars(
        select(Opportunity)
        .where(*filters)
        .order_by(Opportunity.score.desc(), Opportunity.risk_score.asc(), Opportunity.last_seen_at.desc(), Opportunity.opportunity_key.asc(), Opportunity.id.asc())
        .limit(DIGEST_MAX_CANDIDATES)
    ).all()
    evidence = _evidence_context(db, {row.id for row in rows})
    candidates: list[DigestItem] = []
    warnings: list[str] = []
    for row in rows:
        evidence_ids, provenance = evidence.get(row.id, ([], DigestEvidenceProvenance.OBSERVED))
        candidates.append(_digest_item(row, evidence_ids=evidence_ids, provenance=provenance))
    if total > DIGEST_MAX_CANDIDATES:
        warnings.append(f"candidate set truncated to {DIGEST_MAX_CANDIDATES}")
    items = deduplicate_and_rank_digest_items(candidates, policy=policy)
    signature = build_digest_input_signature(
        digest_date=day,
        window_start=window_start,
        window_end=window_end,
        candidates=candidates,
        selection_policy=policy,
    )
    return DailyDigest(
        contract_version=DIGEST_CONTRACT_VERSION,
        algorithm_version=DIGEST_ALGORITHM_VERSION,
        digest_date=day,
        window_start=window_start,
        window_end=window_end,
        generated_at=now,
        status=DigestStatus.READY if items else DigestStatus.EMPTY,
        selection_policy=policy,
        total_candidates=min(total, DIGEST_MAX_CANDIDATES),
        selected_count=len(items),
        input_signature=signature,
        items=items,
        warnings=warnings,
    )
