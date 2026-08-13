from __future__ import annotations

import hashlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import NormalizedItem, RawObservation

_space_re = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _space_re.sub(" ", value.strip())


def canonical_item_key(raw: RawObservation) -> str:
    basis = raw.external_id or f"{normalize_text(raw.title).lower()}|{raw.source_url or ''}"
    return hashlib.sha256(f"{raw.source_id}|{basis}".encode("utf-8")).hexdigest()


def normalize_one(db: Session, raw: RawObservation) -> NormalizedItem:
    existing = db.scalar(select(NormalizedItem).where(NormalizedItem.raw_observation_id == raw.id))
    if existing:
        return existing
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=canonical_item_key(raw),
        source_id=raw.source_id,
        query=normalize_text(raw.query),
        item_type=raw.item_type,
        title=normalize_text(raw.title),
        text=normalize_text(raw.text),
        source_url=raw.source_url,
        observed_at=raw.observed_at,
    )
    db.add(item)
    db.flush()
    return item
