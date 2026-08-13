from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import SourceHealthState

FAILURE_THRESHOLD = 3
CIRCUIT_MINUTES = 30


def get_or_create_source_health(db: Session, source_id: str, *, lock: bool = False) -> SourceHealthState:
    stmt = select(SourceHealthState).where(SourceHealthState.source_id == source_id)
    if lock and db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if row is None:
        candidate = SourceHealthState(source_id=source_id, status="UNKNOWN", updated_at=utc_now())
        try:
            with db.begin_nested():
                db.add(candidate)
                db.flush()
            row = candidate
        except IntegrityError:
            # Another worker created the health row between our read and insert.
            stmt = select(SourceHealthState).where(SourceHealthState.source_id == source_id)
            if lock and db.get_bind().dialect.name == "postgresql":
                stmt = stmt.with_for_update()
            row = db.scalar(stmt)
            if row is None:
                raise
    return row


def circuit_open_until(db: Session, source_id: str):
    row = db.get(SourceHealthState, source_id)
    if row is None or row.circuit_open_until is None:
        return None
    now = utc_now()
    if row.circuit_open_until <= now:
        row.circuit_open_until = None
        row.status = "DEGRADED" if row.consecutive_failures else "HEALTHY"
        row.updated_at = now
        db.flush()
        return None
    return row.circuit_open_until


def _record_run_metrics(
    row: SourceHealthState,
    *,
    duration_ms: int | None,
    fetched: int = 0,
    inserted: int = 0,
) -> None:
    previous_runs = row.total_runs
    row.total_runs += 1
    if duration_ms is not None:
        duration_ms = max(0, int(duration_ms))
        row.last_duration_ms = duration_ms
        if previous_runs <= 0:
            row.avg_duration_ms = float(duration_ms)
        else:
            row.avg_duration_ms = round(
                ((row.avg_duration_ms * previous_runs) + duration_ms) / row.total_runs,
                2,
            )
    row.last_fetched = max(0, int(fetched))
    row.last_inserted = max(0, int(inserted))


def record_success(
    db: Session,
    source_id: str,
    *,
    duration_ms: int | None = None,
    fetched: int = 0,
    inserted: int = 0,
) -> SourceHealthState:
    now = utc_now()
    row = get_or_create_source_health(db, source_id, lock=True)
    _record_run_metrics(row, duration_ms=duration_ms, fetched=fetched, inserted=inserted)
    row.successful_runs += 1
    row.status = "HEALTHY"
    row.consecutive_failures = 0
    row.last_success_at = now
    row.circuit_open_until = None
    row.last_error = None
    row.updated_at = now
    db.flush()
    return row


def record_failure(
    db: Session,
    source_id: str,
    error: str,
    *,
    duration_ms: int | None = None,
) -> SourceHealthState:
    now = utc_now()
    row = get_or_create_source_health(db, source_id, lock=True)
    _record_run_metrics(row, duration_ms=duration_ms)
    row.failed_runs += 1
    row.consecutive_failures += 1
    row.last_failure_at = now
    row.last_error = error[:20_000]
    if row.consecutive_failures >= FAILURE_THRESHOLD:
        row.status = "CIRCUIT_OPEN"
        row.circuit_open_until = now + timedelta(minutes=CIRCUIT_MINUTES)
    else:
        row.status = "DEGRADED"
    row.updated_at = now
    db.flush()
    return row


def record_rate_limited(
    db: Session,
    source_id: str,
    error: str,
    *,
    retry_at: datetime,
    duration_ms: int | None = None,
) -> SourceHealthState:
    now = utc_now()
    row = get_or_create_source_health(db, source_id, lock=True)
    _record_run_metrics(row, duration_ms=duration_ms)
    row.failed_runs += 1
    row.rate_limited_runs += 1
    row.consecutive_failures += 1
    row.last_failure_at = now
    row.last_error = error[:20_000]
    row.status = "CIRCUIT_OPEN"
    row.circuit_open_until = max(retry_at, now + timedelta(minutes=1))
    row.updated_at = now
    db.flush()
    return row


def source_health_report(db: Session, source_ids: list[str]) -> list[dict]:
    existing = {
        row.source_id: row
        for row in db.scalars(select(SourceHealthState).where(SourceHealthState.source_id.in_(source_ids))).all()
    } if source_ids else {}
    now = utc_now()
    result = []
    for source_id in source_ids:
        row = existing.get(source_id)
        if row is None:
            result.append({
                "source_id": source_id,
                "status": "UNKNOWN",
                "consecutive_failures": 0,
                "last_success_at": None,
                "last_failure_at": None,
                "circuit_open_until": None,
                "last_error": None,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "rate_limited_runs": 0,
                "last_duration_ms": None,
                "avg_duration_ms": 0.0,
                "last_fetched": 0,
                "last_inserted": 0,
            })
            continue
        status = row.status
        circuit_until = row.circuit_open_until
        if circuit_until is not None and circuit_until <= now and status == "CIRCUIT_OPEN":
            status = "DEGRADED"
            circuit_until = None
        success_rate = round((row.successful_runs / row.total_runs) * 100.0, 2) if row.total_runs else None
        result.append({
            "source_id": row.source_id,
            "status": status,
            "consecutive_failures": row.consecutive_failures,
            "last_success_at": row.last_success_at,
            "last_failure_at": row.last_failure_at,
            "circuit_open_until": circuit_until,
            "last_error": row.last_error,
            "total_runs": row.total_runs,
            "successful_runs": row.successful_runs,
            "failed_runs": row.failed_runs,
            "rate_limited_runs": row.rate_limited_runs,
            "success_rate_pct": success_rate,
            "last_duration_ms": row.last_duration_ms,
            "avg_duration_ms": row.avg_duration_ms,
            "last_fetched": row.last_fetched,
            "last_inserted": row.last_inserted,
        })
    return result
