"""Auditable invariants for the Observation -> NormalizedItem boundary."""

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import KeywordMention, NormalizedItem, RawObservation
from app.domain.schemas import CollectedRecord
from app.services.ingestion import _content_hash
from app.services.normalizer import canonical_item_key, normalize_text

NORMALIZATION_CONTRACT_VERSION = "normalization-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _expected_hash(raw: RawObservation) -> str:
    record = CollectedRecord(
        external_id=raw.external_id,
        item_type=raw.item_type,
        title=raw.title,
        text=raw.text,
        url=raw.source_url,
        observed_at=raw.observed_at,
        payload=raw.raw_payload or {},
    )
    return _content_hash(
        raw.source_id,
        raw.query,
        record,
        {
            "app_package": raw.app_package,
            "app_version": raw.app_version,
            "instrumentation_version": raw.instrumentation_version,
        },
    )


def audit_observation_normalization(db: Session) -> dict:
    """Return a deterministic report; any violation makes the report fail."""

    violations: list[dict] = []
    raws = db.scalars(select(RawObservation).order_by(RawObservation.id)).all()
    items = db.scalars(select(NormalizedItem).order_by(NormalizedItem.id)).all()
    item_by_raw = {item.raw_observation_id: item for item in items}
    raw_hashes = Counter(raw.content_hash for raw in raws)
    duplicate_hashes = sorted(hash_value for hash_value, count in raw_hashes.items() if count > 1)
    if duplicate_hashes:
        violations.append({"rule": "unique_content_hash", "detail": f"duplicate hashes: {duplicate_hashes}"})

    for raw in raws:
        if not _SHA256_RE.fullmatch(raw.content_hash or ""):
            violations.append({"rule": "content_hash_format", "raw_observation_id": raw.id})
            continue
        try:
            expected_hash = _expected_hash(raw)
        except (TypeError, ValueError):
            violations.append({"rule": "content_hash_recomputable", "raw_observation_id": raw.id})
        else:
            if expected_hash != raw.content_hash:
                violations.append({"rule": "content_hash_matches_payload", "raw_observation_id": raw.id})

        item = item_by_raw.get(raw.id)
        if item is None:
            violations.append({"rule": "raw_has_one_normalized_item", "raw_observation_id": raw.id})
            continue
        expected_fields = {
            "source_id": raw.source_id,
            "query": normalize_text(raw.query),
            "item_type": raw.item_type,
            "title": normalize_text(raw.title),
            "text": normalize_text(raw.text),
            "source_url": raw.source_url,
            "observed_at": raw.observed_at,
            "canonical_key": canonical_item_key(raw),
        }
        for field, expected in expected_fields.items():
            if getattr(item, field) != expected:
                violations.append({"rule": "normalized_field_mirror", "raw_observation_id": raw.id, "field": field})

    raw_ids = {raw.id for raw in raws}
    orphan_items = sorted(item.id for item in items if item.raw_observation_id not in raw_ids)
    if orphan_items:
        violations.append({"rule": "normalized_item_has_raw", "normalized_item_ids": orphan_items})

    duplicate_mentions = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.normalized_item_id, func.count(KeywordMention.id))
        .group_by(KeywordMention.keyword_id, KeywordMention.normalized_item_id)
        .having(func.count(KeywordMention.id) > 1)
    ).all()
    if duplicate_mentions:
        violations.append({"rule": "keyword_mention_idempotency", "pairs": [list(row) for row in duplicate_mentions]})

    return {
        "audit_id": "opportunity-radar-observation-normalization",
        "contract_version": NORMALIZATION_CONTRACT_VERSION,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
        "summary": {
            "raw_observations": len(raws),
            "normalized_items": len(items),
            "normalized_coverage": len(item_by_raw) / len(raws) if raws else 1.0,
            "duplicate_content_hashes": len(duplicate_hashes),
            "keyword_mention_duplicate_pairs": len(duplicate_mentions),
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
