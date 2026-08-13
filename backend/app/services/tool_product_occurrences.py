"""Classify materialized tool/product evidence as first-seen or duplicate."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import ToolProductEntity, ToolProductEntityEvidence, ToolProductOccurrence
from app.domain.tool_product import TOOL_PRODUCT_ALGORITHM_VERSION, TOOL_PRODUCT_CONTRACT_VERSION

TOOL_PRODUCT_OCCURRENCE_MAX_ROWS = 500
FIRST_SEEN = "FIRST_SEEN"
DUPLICATE = "DUPLICATE"


def _occurrence_key(entity_key: str, evidence_id: str) -> str:
    return hashlib.sha256(
        json.dumps({"entity_key": entity_key, "evidence_id": evidence_id}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def materialize_tool_product_occurrences(
    db: Session,
    *,
    entity_keys: set[str] | None = None,
    limit: int = TOOL_PRODUCT_OCCURRENCE_MAX_ROWS,
    detected_at: datetime | None = None,
) -> dict:
    """Persist one stable classification for each entity/evidence occurrence."""

    if limit < 1 or limit > TOOL_PRODUCT_OCCURRENCE_MAX_ROWS:
        raise ValueError(f"limit must be between 1 and {TOOL_PRODUCT_OCCURRENCE_MAX_ROWS}")
    stmt = (
        select(ToolProductEntity, ToolProductEntityEvidence)
        .join(ToolProductEntityEvidence, ToolProductEntityEvidence.entity_id == ToolProductEntity.id)
        .where(ToolProductEntity.status == "IDENTIFIED")
        .order_by(ToolProductEntity.id.asc(), ToolProductEntityEvidence.observed_at.asc(), ToolProductEntityEvidence.id.asc())
        .limit(limit)
    )
    if entity_keys is not None:
        if not entity_keys:
            return {"evaluated": 0, "first_seen": 0, "duplicates": 0, "already_materialized": 0}
        stmt = stmt.where(ToolProductEntity.entity_key.in_(entity_keys))
    rows = db.execute(stmt).all()
    if not rows:
        return {"evaluated": 0, "first_seen": 0, "duplicates": 0, "already_materialized": 0}

    entity_ids = {entity.id for entity, _evidence in rows}
    existing = db.scalars(
        select(ToolProductOccurrence).where(ToolProductOccurrence.entity_id.in_(entity_ids))
    ).all()
    existing_by_item = {(row.entity_id, row.normalized_item_id): row for row in existing}
    first_seen_entities = {row.entity_id for row in existing if row.classification == FIRST_SEEN}
    now = detected_at or utc_now()
    first_seen = 0
    duplicates = 0
    already_materialized = 0
    for entity, evidence in rows:
        pair = (entity.id, evidence.normalized_item_id)
        if pair in existing_by_item:
            already_materialized += 1
            continue
        classification = DUPLICATE if entity.id in first_seen_entities else FIRST_SEEN
        db.add(ToolProductOccurrence(
            entity_id=entity.id,
            normalized_item_id=evidence.normalized_item_id,
            occurrence_key=_occurrence_key(entity.entity_key, evidence.evidence_id),
            classification=classification,
            evidence_id=evidence.evidence_id,
            source_id=evidence.source_id,
            observed_at=evidence.observed_at,
            contract_version=TOOL_PRODUCT_CONTRACT_VERSION,
            algorithm_version=TOOL_PRODUCT_ALGORITHM_VERSION,
            input_signature=entity.latest_input_signature,
            detected_at=now,
            created_at=now,
        ))
        existing_by_item[pair] = True
        if classification == FIRST_SEEN:
            first_seen_entities.add(entity.id)
            first_seen += 1
        else:
            duplicates += 1
    db.flush()
    return {
        "evaluated": len(rows),
        "first_seen": first_seen,
        "duplicates": duplicates,
        "already_materialized": already_materialized,
        "contract_version": TOOL_PRODUCT_CONTRACT_VERSION,
        "algorithm_version": TOOL_PRODUCT_ALGORITHM_VERSION,
    }


def list_tool_product_occurrences(
    db: Session,
    *,
    entity_key: str | None = None,
    classification: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = (
        select(ToolProductOccurrence, ToolProductEntity)
        .join(ToolProductEntity, ToolProductEntity.id == ToolProductOccurrence.entity_id)
        .order_by(ToolProductOccurrence.observed_at.asc(), ToolProductOccurrence.id.asc())
        .limit(max(1, min(500, limit)))
    )
    if entity_key:
        stmt = stmt.where(ToolProductEntity.entity_key == entity_key.strip())
    if classification:
        stmt = stmt.where(ToolProductOccurrence.classification == classification.strip().upper())
    return [
        {
            "id": occurrence.id,
            "entity_id": occurrence.entity_id,
            "entity_key": entity.entity_key,
            "display_name": entity.display_name,
            "classification": occurrence.classification,
            "normalized_item_id": occurrence.normalized_item_id,
            "occurrence_key": occurrence.occurrence_key,
            "evidence_id": occurrence.evidence_id,
            "source_id": occurrence.source_id,
            "observed_at": occurrence.observed_at,
            "contract_version": occurrence.contract_version,
            "algorithm_version": occurrence.algorithm_version,
            "input_signature": occurrence.input_signature,
            "detected_at": occurrence.detected_at,
        }
        for occurrence, entity in db.execute(stmt).all()
    ]
