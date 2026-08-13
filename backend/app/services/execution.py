from __future__ import annotations

from datetime import timedelta
from time import perf_counter

from sqlalchemy.orm import Session

from app.connectors.base import ConnectorRateLimitError
from app.connectors.registry import SourceRegistry
from app.core.time import utc_now
from app.db.models import CollectionRun
from app.domain.enums import CollectionRunStatus, QueryMode
from app.domain.schemas import CollectorQuery
from app.services.pipeline import collect_and_process
from app.services.source_preferences import source_enabled
from app.services.source_health import (
    circuit_open_until,
    record_failure,
    record_rate_limited,
    record_success,
)


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((perf_counter() - started) * 1000)))


def execute_collection(
    db: Session,
    registry: SourceRegistry,
    *,
    source_id: str,
    query: CollectorQuery,
    intent: str | None = None,
    probe_task_id: int | None = None,
    worker_id: str | None = None,
) -> dict:
    connector = registry.get(source_id)
    descriptor = connector.descriptor
    if not descriptor.enabled or not source_enabled(db, source_id, default=descriptor.enabled):
        raise ValueError(f"source is disabled: {source_id}")
    if descriptor.query_mode == QueryMode.PUSH_ONLY:
        raise ValueError(f"source is push-only and cannot be actively collected: {source_id}")

    open_until = circuit_open_until(db, source_id)
    if open_until is not None:
        run = CollectionRun(
            probe_task_id=probe_task_id,
            source_id=source_id,
            query=query.query,
            intent=intent,
            worker_id=worker_id,
            status=CollectionRunStatus.SKIPPED.value,
            started_at=utc_now(),
            finished_at=utc_now(),
            duration_ms=0,
            error=f"source circuit open until {open_until.isoformat()}",
        )
        db.add(run)
        db.commit()
        return {
            "source_id": source_id,
            "query": query.query,
            "fetched": 0,
            "inserted": 0,
            "duplicates": 0,
            "normalized": 0,
            "run_id": run.id,
            "status": CollectionRunStatus.SKIPPED.value,
            "circuit_open_until": open_until,
            "duration_ms": 0,
        }

    run = CollectionRun(
        probe_task_id=probe_task_id,
        source_id=source_id,
        query=query.query,
        intent=intent,
        worker_id=worker_id,
        status=CollectionRunStatus.RUNNING.value,
        started_at=utc_now(),
    )
    db.add(run)
    db.commit()
    run_id = run.id
    started = perf_counter()

    try:
        result = collect_and_process(db, connector, query)
        duration_ms = _elapsed_ms(started)
        run = db.get(CollectionRun, run_id)
        if run is None:
            raise RuntimeError(f"collection run disappeared: {run_id}")
        run.status = CollectionRunStatus.SUCCEEDED.value
        run.finished_at = utc_now()
        run.duration_ms = duration_ms
        run.fetched = result["fetched"]
        run.inserted = result["inserted"]
        run.duplicates = result["duplicates"]
        run.normalized = result["normalized"]
        record_success(
            db,
            source_id,
            duration_ms=duration_ms,
            fetched=result["fetched"],
            inserted=result["inserted"],
        )
        db.commit()
        return {**result, "run_id": run_id, "status": run.status, "duration_ms": duration_ms}
    except ConnectorRateLimitError as exc:
        duration_ms = _elapsed_ms(started)
        db.rollback()
        failed_run = db.get(CollectionRun, run_id)
        if failed_run is not None:
            failed_run.status = CollectionRunStatus.FAILED.value
            failed_run.finished_at = utc_now()
            failed_run.duration_ms = duration_ms
            failed_run.error = str(exc)[:20_000]
        retry_at = utc_now() + timedelta(seconds=exc.retry_after_seconds)
        record_rate_limited(
            db,
            source_id,
            str(exc),
            retry_at=retry_at,
            duration_ms=duration_ms,
        )
        db.commit()
        raise
    except Exception as exc:
        duration_ms = _elapsed_ms(started)
        db.rollback()
        failed_run = db.get(CollectionRun, run_id)
        if failed_run is not None:
            failed_run.status = CollectionRunStatus.FAILED.value
            failed_run.finished_at = utc_now()
            failed_run.duration_ms = duration_ms
            failed_run.error = str(exc)[:20_000]
        record_failure(db, source_id, str(exc), duration_ms=duration_ms)
        db.commit()
        raise
