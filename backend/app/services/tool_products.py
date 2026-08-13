"""Materialize auditable multi-source tool/product entities from normalized evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    NormalizedItem,
    RawObservation,
    ToolProductEntity,
    ToolProductEntityEvidence,
    ToolProductNormalizationRun,
)
from app.domain.citations import evidence_id_for_content_hash, provenance_from_payload
from app.domain.enums import ItemType
from app.domain.tool_product import (
    TOOL_PRODUCT_ALGORITHM_VERSION,
    TOOL_PRODUCT_CONTRACT_VERSION,
    ToolProductEvidence,
    ToolProductIdentificationInput,
    ToolProductIdentificationPolicy,
    ToolProductKind,
    ToolProductStatus,
    identify_tool_product,
    normalize_tool_product_name,
)

TOOL_PRODUCT_MAX_ITEMS = 500


def _candidate_kind(item_type: str) -> ToolProductKind | None:
    normalized = str(item_type or "").strip().upper()
    if normalized == ItemType.PRODUCT.value:
        return ToolProductKind.PRODUCT
    if normalized == ItemType.APP_OBSERVATION.value:
        return ToolProductKind.TOOL
    return None


def _candidate_key(name: str, claimed_kind: ToolProductKind | None) -> str:
    payload = {
        "name": normalize_tool_product_name(name),
        "claimed_kind": claimed_kind.value if claimed_kind else None,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _evidence(item: NormalizedItem, raw: RawObservation) -> ToolProductEvidence:
    return ToolProductEvidence(
        evidence_id=evidence_id_for_content_hash(raw.content_hash),
        source=item.source_id,
        title=(item.title or "")[:500],
        text=(item.text or "")[:2_000],
        item_type=item.item_type,
        observed_at=item.observed_at,
        provenance=provenance_from_payload(raw.raw_payload),
        source_url=(item.source_url or "")[:2_000] or None,
    )


def _run_row(result, *, candidate_key: str) -> ToolProductNormalizationRun:
    return ToolProductNormalizationRun(
        candidate_key=candidate_key,
        entity_key=result.entity_key,
        display_name=result.display_name,
        kind=result.kind.value,
        status=result.status.value,
        confidence=result.confidence,
        contract_version=result.contract_version,
        algorithm_version=result.algorithm_version,
        policy_version=result.policy.policy_version,
        evidence_count=result.evidence_count,
        deduplicated_count=result.deduplicated_count,
        source_count=result.source_count,
        evidence_ids=list(result.evidence_ids),
        reasons=list(result.reasons),
        input_signature=result.input_signature,
        evaluated_at=result.evaluated_at,
        created_at=result.evaluated_at,
    )


def _entity_row(result, *, now: datetime) -> ToolProductEntity:
    assert result.entity_key is not None
    assert result.display_name is not None
    return ToolProductEntity(
        entity_key=result.entity_key,
        display_name=result.display_name,
        normalized_name=normalize_tool_product_name(result.display_name),
        kind=result.kind.value,
        status=result.status.value,
        confidence=result.confidence,
        contract_version=result.contract_version,
        algorithm_version=result.algorithm_version,
        policy_version=result.policy.policy_version,
        evidence_count=result.evidence_count,
        source_count=result.source_count,
        evidence_ids=list(result.evidence_ids),
        first_seen_at=result.first_seen_at,
        last_seen_at=result.last_seen_at,
        latest_input_signature=result.input_signature,
        evaluated_at=result.evaluated_at,
        created_at=now,
        updated_at=now,
    )


def _entity_dict(entity: ToolProductEntity) -> dict:
    return {
        "id": entity.id,
        "entity_key": entity.entity_key,
        "display_name": entity.display_name,
        "normalized_name": entity.normalized_name,
        "kind": entity.kind,
        "status": entity.status,
        "confidence": entity.confidence,
        "contract_version": entity.contract_version,
        "algorithm_version": entity.algorithm_version,
        "policy_version": entity.policy_version,
        "evidence_count": entity.evidence_count,
        "source_count": entity.source_count,
        "evidence_ids": entity.evidence_ids or [],
        "first_seen_at": entity.first_seen_at,
        "last_seen_at": entity.last_seen_at,
        "latest_input_signature": entity.latest_input_signature,
        "evaluated_at": entity.evaluated_at,
        "created_at": entity.created_at,
        "updated_at": entity.updated_at,
    }


def _load_items(db: Session, *, normalized_item_ids: set[int] | None, limit: int) -> list[tuple[NormalizedItem, RawObservation]]:
    stmt = (
        select(NormalizedItem, RawObservation)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
        .limit(limit)
    )
    if normalized_item_ids is not None:
        if not normalized_item_ids:
            return []
        seed_rows = db.execute(
            select(NormalizedItem.title, NormalizedItem.query)
            .where(NormalizedItem.id.in_(normalized_item_ids))
        ).all()
        names = {normalize_tool_product_name(title or query) for title, query in seed_rows if normalize_tool_product_name(title or query)}
        if not names:
            return []
        # Re-load every source's matching candidate so a second ingestion joins
        # the existing entity instead of creating a source-local identity.
        stmt = stmt.where(NormalizedItem.title.is_not(None))
        candidates = db.execute(
            select(NormalizedItem.id).where(NormalizedItem.id.in_(normalized_item_ids))
        ).all()
        if candidates:
            all_rows = db.execute(
                select(NormalizedItem, RawObservation)
                .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
                .order_by(NormalizedItem.observed_at.desc(), NormalizedItem.id.desc())
            ).all()
            return [
                (item, raw)
                for item, raw in all_rows
                if normalize_tool_product_name(item.title or item.query) in names
            ][:limit]
        return []
    return db.execute(stmt).all()


def normalize_tool_product_entities(
    db: Session,
    *,
    normalized_item_ids: set[int] | None = None,
    policy: ToolProductIdentificationPolicy | None = None,
    limit: int = TOOL_PRODUCT_MAX_ITEMS,
    evaluated_at: datetime | None = None,
) -> dict:
    """Identify and upsert entities from bounded normalized evidence.

    The operation is deterministic for the same evidence set, persists every
    decision in a run table, and links successful entities back to immutable
    citation IDs plus normalized item IDs. No external provider is called.
    """

    if limit < 1 or limit > TOOL_PRODUCT_MAX_ITEMS:
        raise ValueError(f"limit must be between 1 and {TOOL_PRODUCT_MAX_ITEMS}")
    policy = policy or ToolProductIdentificationPolicy()
    rows = _load_items(db, normalized_item_ids=normalized_item_ids, limit=limit)
    grouped: dict[tuple[str, str | None], dict] = {}
    for item, raw in rows:
        name = (item.title or item.query or "").strip()[:300]
        normalized_name = normalize_tool_product_name(name)
        if not normalized_name:
            continue
        claimed_kind = _candidate_kind(item.item_type)
        group_key = (normalized_name, claimed_kind.value if claimed_kind else None)
        group = grouped.setdefault(
            group_key,
            {"name": name, "claimed_kind": claimed_kind, "items": [], "evidence": []},
        )
        group["items"].append((item, raw))
        group["evidence"].append(_evidence(item, raw))

    evaluated = 0
    identified = 0
    low_confidence = 0
    unresolved = 0
    insufficient = 0
    duplicates = 0
    evidence_links = 0
    evaluation_time = evaluated_at or utc_now()
    for group in grouped.values():
        evidence_rows = sorted(
            zip(group["evidence"], group["items"]),
            key=lambda pair: (pair[0].observed_at, pair[0].evidence_id),
        )[-policy.max_evidence:]
        evidence = [pair[0] for pair in evidence_rows]
        result = identify_tool_product(
            ToolProductIdentificationInput(
                candidate_name=group["name"],
                claimed_kind=group["claimed_kind"],
                evidence=evidence,
            ),
            policy=policy,
            evaluated_at=evaluation_time,
        )
        evaluated += 1
        existing_run = db.scalar(
            select(ToolProductNormalizationRun).where(ToolProductNormalizationRun.input_signature == result.input_signature)
        )
        if existing_run is not None:
            duplicates += 1
            continue
        db.add(_run_row(result, candidate_key=_candidate_key(group["name"], group["claimed_kind"])))
        if result.status == ToolProductStatus.IDENTIFIED:
            identified += 1
        elif result.status == ToolProductStatus.LOW_CONFIDENCE:
            low_confidence += 1
        elif result.status == ToolProductStatus.UNRESOLVED:
            unresolved += 1
        else:
            insufficient += 1
        if result.entity_key is None:
            continue
        entity = db.scalar(select(ToolProductEntity).where(ToolProductEntity.entity_key == result.entity_key))
        now = evaluation_time
        if entity is None:
            entity = _entity_row(result, now=now)
            db.add(entity)
            db.flush()
        else:
            entity.display_name = result.display_name or entity.display_name
            entity.normalized_name = normalize_tool_product_name(entity.display_name)
            entity.kind = result.kind.value
            entity.status = result.status.value
            entity.confidence = result.confidence
            entity.contract_version = result.contract_version
            entity.algorithm_version = result.algorithm_version
            entity.policy_version = result.policy.policy_version
            entity.evidence_count = result.evidence_count
            entity.source_count = result.source_count
            entity.evidence_ids = list(result.evidence_ids)
            entity.first_seen_at = min(filter(None, [entity.first_seen_at, result.first_seen_at]), default=None)
            entity.last_seen_at = max(filter(None, [entity.last_seen_at, result.last_seen_at]), default=None)
            entity.latest_input_signature = result.input_signature
            entity.evaluated_at = result.evaluated_at
            entity.updated_at = now
            db.flush()
        existing_evidence_ids = set(db.scalars(
            select(ToolProductEntityEvidence.evidence_id).where(ToolProductEntityEvidence.entity_id == entity.id)
        ).all())
        for row, (item, _raw) in evidence_rows:
            if row.evidence_id in existing_evidence_ids:
                continue
            db.add(ToolProductEntityEvidence(
                entity_id=entity.id,
                normalized_item_id=item.id,
                evidence_id=row.evidence_id,
                source_id=row.source,
                observed_at=row.observed_at,
                created_at=now,
            ))
            existing_evidence_ids.add(row.evidence_id)
            evidence_links += 1
    db.flush()
    return {
        "contract_version": TOOL_PRODUCT_CONTRACT_VERSION,
        "algorithm_version": TOOL_PRODUCT_ALGORITHM_VERSION,
        "evaluated": evaluated,
        "identified": identified,
        "low_confidence": low_confidence,
        "unresolved": unresolved,
        "insufficient_evidence": insufficient,
        "duplicates": duplicates,
        "evidence_links": evidence_links,
        "input_limit": limit,
    }


def list_tool_product_entities(
    db: Session,
    *,
    status: str | None = None,
    kind: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = select(ToolProductEntity)
    if status:
        stmt = stmt.where(ToolProductEntity.status == status.strip().upper())
    if kind:
        stmt = stmt.where(ToolProductEntity.kind == kind.strip().upper())
    rows = db.scalars(stmt.order_by(ToolProductEntity.updated_at.desc(), ToolProductEntity.id.desc()).limit(max(1, min(500, limit)))).all()
    return [_entity_dict(row) for row in rows]


def tool_product_entity_detail(db: Session, entity_key: str) -> dict:
    entity = db.scalar(select(ToolProductEntity).where(ToolProductEntity.entity_key == entity_key.strip()))
    if entity is None:
        raise KeyError(f"unknown tool/product entity: {entity_key}")
    evidence_rows = db.scalars(
        select(ToolProductEntityEvidence)
        .where(ToolProductEntityEvidence.entity_id == entity.id)
        .order_by(ToolProductEntityEvidence.observed_at.desc(), ToolProductEntityEvidence.id.desc())
    ).all()
    return {
        **_entity_dict(entity),
        "evidence": [
            {
                "id": row.id,
                "normalized_item_id": row.normalized_item_id,
                "evidence_id": row.evidence_id,
                "source_id": row.source_id,
                "observed_at": row.observed_at,
                "created_at": row.created_at,
            }
            for row in evidence_rows
        ],
    }
