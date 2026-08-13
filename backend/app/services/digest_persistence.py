"""Persistence and reconstruction of the versioned daily digest contract."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import DailyDigestRecord
from app.domain.digest import DailyDigest


def _payload_for_digest(digest: DailyDigest) -> dict:
    data = digest.model_dump(mode="json")
    return {
        "items": data["items"],
        "warnings": data["warnings"],
        "generation_error": data["generation_error"],
    }


def _contract_for_record(row: DailyDigestRecord) -> DailyDigest:
    payload = row.payload or {}
    return DailyDigest.model_validate({
        "contract_version": row.contract_version,
        "algorithm_version": row.algorithm_version,
        "digest_date": row.digest_date,
        "timezone": row.timezone,
        "window_start": row.window_start,
        "window_end": row.window_end,
        "generated_at": row.generated_at,
        "status": row.status,
        "selection_policy": row.selection_policy or {},
        "total_candidates": row.total_candidates,
        "selected_count": row.selected_count,
        "input_signature": row.input_signature,
        "items": payload.get("items", []),
        "warnings": payload.get("warnings", []),
        "generation_error": payload.get("generation_error"),
    })


def save_daily_digest(db: Session, digest: DailyDigest) -> DailyDigestRecord:
    """Upsert one UTC date; repeated same-input generation is idempotent."""

    row = db.scalar(select(DailyDigestRecord).where(DailyDigestRecord.digest_date == digest.digest_date))
    now = utc_now()
    data = digest.model_dump(mode="json")
    if row is None:
        row = DailyDigestRecord(
            digest_date=digest.digest_date,
            contract_version=digest.contract_version,
            algorithm_version=digest.algorithm_version,
            timezone=digest.timezone,
            window_start=digest.window_start,
            window_end=digest.window_end,
            generated_at=digest.generated_at,
            status=digest.status.value,
            selection_policy=data["selection_policy"],
            total_candidates=digest.total_candidates,
            selected_count=digest.selected_count,
            input_signature=digest.input_signature,
            payload=_payload_for_digest(digest),
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    elif row.input_signature != digest.input_signature or row.contract_version != digest.contract_version:
        row.contract_version = digest.contract_version
        row.algorithm_version = digest.algorithm_version
        row.timezone = digest.timezone
        row.window_start = digest.window_start
        row.window_end = digest.window_end
        row.generated_at = digest.generated_at
        row.status = digest.status.value
        row.selection_policy = data["selection_policy"]
        row.total_candidates = digest.total_candidates
        row.selected_count = digest.selected_count
        row.input_signature = digest.input_signature
        row.payload = _payload_for_digest(digest)
        row.updated_at = now
    db.flush()
    return row


def get_daily_digest(db: Session, digest_date: date | None = None) -> DailyDigest:
    stmt = select(DailyDigestRecord)
    if digest_date is None:
        stmt = stmt.order_by(DailyDigestRecord.digest_date.desc()).limit(1)
        row = db.scalar(stmt)
    else:
        row = db.scalar(stmt.where(DailyDigestRecord.digest_date == digest_date))
    if row is None:
        raise KeyError("daily digest not found")
    return _contract_for_record(row)
