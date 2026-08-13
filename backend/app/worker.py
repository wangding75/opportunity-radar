from __future__ import annotations

import argparse
import os
import socket
import time

from app.connectors.registry import SourceRegistry, build_default_registry
from app.core.config import settings, validate_runtime_settings
from app.core.observability import configure_logging
from app.db.session import SessionLocal, engine
from app.services.alerts import run_pending_alert_evaluations
from app.services.keyword_burst_alerts import materialize_keyword_burst_alerts
from app.services.tool_product_alerts import materialize_tool_product_alerts
from app.services.hiring_surge_alerts import materialize_hiring_surge_alerts
from app.services.cross_source_confirmations import materialize_cross_source_confirmations
from app.services.cross_source_alerts import materialize_cross_source_alerts
from app.services.score_jumps import materialize_score_jumps
from app.services.score_jump_alerts import materialize_score_jump_alerts
from app.services.risk_escalation_alerts import materialize_risk_escalations
from app.services.email_delivery_queue import enqueue_alert_emails, process_email_delivery_queue
from app.services.webhook_delivery_queue import enqueue_alert_webhooks, process_webhook_delivery_queue
from app.services.analysis import refresh_derived_analysis
from app.services.analysis_queue import run_pending_opportunity_analysis
from app.services.probes import run_due_probe_tasks, sync_probe_tasks
from app.services.retention import run_retention
from app.services.archive import archive_raw_payloads
from app.services.auth import cleanup_auth_records
from app.services.digest import generate_daily_digest
from app.services.digest_persistence import save_daily_digest
from app.services.weekly_trends import aggregate_weekly_trends
from app.services.weekly_trend_persistence import save_weekly_trend_report
from app.services.worker_health import touch_worker


def default_worker_id() -> str:
    return os.getenv("WORKER_ID", f"{socket.gethostname()}:{os.getpid()}")[:200]


def _touch_heartbeat(worker_id: str, mode: str, *, status: str = "RUNNING") -> None:
    # Use a dedicated short transaction so heartbeat commits can never commit or
    # roll back business work in the active worker session.
    with SessionLocal() as health_db:
        touch_worker(health_db, worker_id, mode, status=status)


def _touch_progress_heartbeat(worker_id: str, mode: str) -> None:
    # PostgreSQL permits the independent heartbeat transaction while business
    # work is still open. SQLite allows only one writer; a second heartbeat
    # writer would contend with the maintenance transaction and can fail with
    # `database is locked`. Local SQLite therefore updates heartbeat only at
    # safe phase/iteration boundaries after the business transaction releases.
    if engine.dialect.name == "sqlite":
        return
    _touch_heartbeat(worker_id, mode)


def _sleep_with_heartbeat(seconds: int, worker_id: str, mode: str) -> None:
    """Sleep long worker intervals without making a healthy process look stale."""
    remaining = max(0, int(seconds))
    stale_window = settings.maintenance_worker_stale_seconds if mode == "maintenance" else settings.worker_stale_seconds
    heartbeat_chunk = max(10, min(600, stale_window // 2))
    while remaining > 0:
        step = min(heartbeat_chunk, remaining)
        time.sleep(step)
        remaining -= step
        if remaining > 0:
            _touch_heartbeat(worker_id, mode, status="IDLE")


def run_once(
    *,
    sync: bool,
    limit: int,
    mode: str = "all",
    worker_id: str | None = None,
    registry: SourceRegistry | None = None,
) -> dict:
    validate_runtime_settings()
    worker_id = worker_id or default_worker_id()
    owns_registry = registry is None
    active_registry = registry or build_default_registry()
    _touch_heartbeat(worker_id, mode)
    try:
        with SessionLocal() as db:
            result: dict = {"mode": mode, "worker_id": worker_id}
            if mode in {"all", "collection"}:
                result["sync"] = sync_probe_tasks(db, active_registry) if sync else None
                result["runs"] = run_due_probe_tasks(
                    db,
                    active_registry,
                    limit=limit,
                    worker_id=worker_id,
                    progress_callback=lambda: _touch_heartbeat(worker_id, mode),
                )
                _touch_heartbeat(worker_id, mode)
            if mode in {"all", "analysis"}:
                result["analysis"] = run_pending_opportunity_analysis(db, progress_callback=lambda: _touch_heartbeat(worker_id, mode))
                _touch_heartbeat(worker_id, mode)
            if mode in {"all", "alerts"}:
                result["alerts"] = run_pending_alert_evaluations(db, limit=max(50, limit * 20), progress_callback=lambda: _touch_heartbeat(worker_id, mode))
                result["keyword_bursts"] = materialize_keyword_burst_alerts(db, limit=100)
                result["tool_product_alerts"] = materialize_tool_product_alerts(db, limit=500)
                result["hiring_surge_alerts"] = materialize_hiring_surge_alerts(db, limit=100)
                result["cross_source_confirmations"] = materialize_cross_source_confirmations(db, limit=100)
                result["cross_source_alerts"] = materialize_cross_source_alerts(db, limit=100)
                result["score_jumps"] = materialize_score_jumps(db, limit=100)
                result["score_jump_alerts"] = materialize_score_jump_alerts(db, limit=100)
                result["risk_escalations"] = materialize_risk_escalations(db, limit=100)
                if settings.email_delivery_enabled:
                    result["email_delivery_enqueue"] = enqueue_alert_emails(
                        db,
                        recipients=list(settings.email_delivery_recipients),
                        data_class="MOCK" if settings.email_delivery_provider in {"mock", "mock_http"} else "ALERT_EVENT",
                        limit=max(100, limit * 20),
                    )
                    db.commit()
                    result["email_delivery"] = process_email_delivery_queue(db, limit=max(100, limit * 20), progress_callback=lambda: _touch_heartbeat(worker_id, mode))
                else:
                    result["email_delivery"] = {"status": "DISABLED", "processed": 0, "claimed": 0}
                if settings.webhook_delivery_enabled:
                    result["webhook_delivery_enqueue"] = enqueue_alert_webhooks(
                        db,
                        data_class="ALERT_EVENT",
                        limit=max(100, limit * 20),
                    )
                    db.commit()
                    result["webhook_delivery"] = process_webhook_delivery_queue(
                        db,
                        limit=max(100, limit * 20),
                        progress_callback=lambda: _touch_heartbeat(worker_id, mode),
                    )
                else:
                    result["webhook_delivery"] = {"status": "DISABLED", "processed": 0, "claimed": 0}
                db.commit()
                _touch_heartbeat(worker_id, mode)
            if mode == "maintenance":
                result["derived"] = refresh_derived_analysis(db, progress_callback=lambda: _touch_progress_heartbeat(worker_id, mode))
                db.commit()
                _touch_heartbeat(worker_id, mode)
                result["retention"] = run_retention(db, dry_run=False)
                _touch_heartbeat(worker_id, mode)
                result["raw_payload_archive"] = archive_raw_payloads(
                    db,
                    older_than_days=settings.raw_payload_archive_after_days,
                    limit=settings.raw_payload_archive_batch_size,
                    dry_run=False,
                )
                _touch_heartbeat(worker_id, mode)
                result["auth_cleanup"] = cleanup_auth_records(db, retention_days=settings.auth_record_retention_days, dry_run=False)
                _touch_heartbeat(worker_id, mode)
            if mode == "digest":
                digest = generate_daily_digest(db)
                save_daily_digest(db, digest)
                db.commit()
                result["digest"] = digest.model_dump(mode="json")
                _touch_heartbeat(worker_id, mode)
            if mode == "weekly":
                report = aggregate_weekly_trends(db)
                save_weekly_trend_report(db, report)
                db.commit()
                result["weekly_trends"] = report.model_dump(mode="json")
                _touch_heartbeat(worker_id, mode)
        with SessionLocal() as health_db:
            touch_worker(health_db, worker_id, mode, status="IDLE", success=True, increment_iteration=True)
        return result
    except Exception as exc:
        with SessionLocal() as health_db:
            touch_worker(health_db, worker_id, mode, status="ERROR", error=str(exc), increment_iteration=True)
        raise
    finally:
        if owns_registry:
            active_registry.close()


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Opportunity Radar background worker")
    parser.add_argument("--once", action="store_true", help="run one worker iteration and exit")
    parser.add_argument("--interval", type=int, default=60, help="loop interval in seconds (minimum 10)")
    parser.add_argument("--limit", type=int, default=10, help="maximum due probes executed per collection iteration")
    parser.add_argument("--no-sync", action="store_true", help="do not refresh planner-managed probe tasks")
    parser.add_argument("--mode", choices=["all", "collection", "analysis", "alerts", "maintenance", "digest", "weekly"], default="all")
    parser.add_argument("--worker-id", default=None)
    args = parser.parse_args()

    interval = max(10, args.interval)
    limit = max(1, min(100, args.limit))
    worker_id = args.worker_id or default_worker_id()
    if args.once:
        print(run_once(sync=not args.no_sync, limit=limit, mode=args.mode, worker_id=worker_id))
        return 0

    # Persistent workers reuse connector-owned HTTP clients across iterations so
    # connection pooling works and a one-minute loop does not rebuild every client.
    registry = build_default_registry()
    try:
        while True:
            try:
                print(
                    run_once(
                        sync=not args.no_sync,
                        limit=limit,
                        mode=args.mode,
                        worker_id=worker_id,
                        registry=registry,
                    ),
                    flush=True,
                )
            except Exception as exc:
                print({"status": "worker_iteration_failed", "mode": args.mode, "worker_id": worker_id, "error": str(exc)}, flush=True)
            _sleep_with_heartbeat(interval, worker_id, args.mode)
    finally:
        registry.close()


if __name__ == "__main__":
    raise SystemExit(main())
