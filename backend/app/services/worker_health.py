from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.models import WorkerHeartbeat


def touch_worker(
    db: Session,
    worker_id: str,
    mode: str,
    *,
    status: str,
    error: str | None = None,
    success: bool = False,
    increment_iteration: bool = False,
) -> WorkerHeartbeat:
    now = utc_now()
    row = db.get(WorkerHeartbeat, worker_id)
    if row is None:
        row = WorkerHeartbeat(
            worker_id=worker_id,
            mode=mode,
            status=status,
            started_at=now,
            last_seen_at=now,
            iteration_count=0,
        )
        db.add(row)
    row.mode = mode
    row.status = status
    row.last_seen_at = now
    if increment_iteration:
        row.iteration_count = int(row.iteration_count or 0) + 1
    row.last_error = error[:20_000] if error else None
    if success:
        row.last_success_at = now
    db.commit()
    return row


def worker_health_report(db: Session) -> list[dict]:
    now = utc_now()
    rows = db.scalars(select(WorkerHeartbeat).order_by(WorkerHeartbeat.last_seen_at.desc())).all()
    return [
        {
            "worker_id": row.worker_id,
            "mode": row.mode,
            "status": "STALE" if row.last_seen_at < now - timedelta(seconds=(settings.maintenance_worker_stale_seconds if row.mode == "maintenance" else settings.worker_stale_seconds)) else row.status,
            "started_at": row.started_at,
            "last_seen_at": row.last_seen_at,
            "last_success_at": row.last_success_at,
            "iteration_count": row.iteration_count,
            "last_error": row.last_error,
        }
        for row in rows
    ]
