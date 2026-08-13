from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, SeedKeyword
from app.domain.enums import KeywordStatus
from app.services.keywords import canonicalize_keyword, refresh_keyword_metrics


def create_watch_keyword(db: Session, keyword: str, *, priority: int = 3, notes: str = "") -> SeedKeyword:
    display = keyword.strip()
    canonical = canonicalize_keyword(display)
    if len(canonical) < 2:
        raise ValueError("keyword is too short")
    if db.scalar(select(SeedKeyword.id).where(SeedKeyword.canonical == canonical)) is not None:
        raise ValueError("watch keyword already exists")
    now = utc_now()
    row = SeedKeyword(
        canonical=canonical,
        display_name=display[:200],
        enabled=True,
        priority=priority,
        notes=notes[:10_000],
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    kw = db.scalar(select(Keyword).where(Keyword.canonical == canonical))
    if kw is None:
        kw = Keyword(
            canonical=canonical,
            display_name=display[:200],
            status=KeywordStatus.WATCHING.value,
            first_seen_at=now,
            last_seen_at=now,
            score=float(10 + priority * 5),
        )
        db.add(kw)
    elif kw.status in {KeywordStatus.ARCHIVED.value, KeywordStatus.DECLINING.value, KeywordStatus.DISCOVERED.value}:
        kw.status = KeywordStatus.WATCHING.value
        kw.score = max(kw.score, float(10 + priority * 5))
    db.flush()
    refresh_keyword_metrics(db, keyword_ids={kw.id})
    return row


def patch_watch_keyword(db: Session, watch_id: int, *, enabled=None, priority=None, notes=None) -> SeedKeyword:
    row = db.get(SeedKeyword, watch_id)
    if row is None:
        raise KeyError(f"watch keyword not found: {watch_id}")
    if enabled is not None:
        row.enabled = enabled
    if priority is not None:
        row.priority = priority
    if notes is not None:
        row.notes = notes[:10_000]
    row.updated_at = utc_now()
    kw = db.scalar(select(Keyword).where(Keyword.canonical == row.canonical))
    db.flush()
    if kw is not None:
        # Recalculate immediately so disabling a watch removes a stale WATCHING
        # floor, and priority decreases/increases take effect before the next
        # collection or maintenance cycle. Organically active/trending keywords
        # can remain active even after the explicit watch is disabled.
        refresh_keyword_metrics(db, keyword_ids={kw.id})
    return row
