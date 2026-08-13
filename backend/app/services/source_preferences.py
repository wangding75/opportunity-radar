from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import SourcePreference


def get_source_preference(db: Session, source_id: str) -> SourcePreference | None:
    return db.get(SourcePreference, source_id)


def source_enabled(db: Session, source_id: str, *, default: bool = True) -> bool:
    row = db.get(SourcePreference, source_id)
    return default if row is None else bool(row.enabled)


def set_source_preference(db: Session, source_id: str, *, enabled: bool, note: str = "") -> SourcePreference:
    row = db.get(SourcePreference, source_id)
    if row is None:
        row = SourcePreference(source_id=source_id)
        db.add(row)
    row.enabled = enabled
    row.note = note[:10_000]
    row.updated_at = utc_now()
    db.flush()
    return row
