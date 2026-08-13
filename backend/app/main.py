from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import secrets
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.routes import router, set_registry
from app.api.auth import admin_router, router as auth_router
from app.api.scoring import router as scoring_router
from app.api.operations import router as operations_router
from app.api.research import router as research_router
from app.connectors.registry import build_default_registry
from app.core.config import settings, validate_runtime_settings
from app.core.request_limits import RequestBodyLimitMiddleware
from app.core.security import require_read_auth
from app.db.models import AuditLog
from app.db.session import SessionLocal, engine
from app.core.time import utc_now
from app.core.observability import configure_logging, metrics, render_database_metrics
from app.services.sanitizer import sanitize_query
from app.services.api_permissions import attach_openapi_permissions
import uuid

LOGGER = logging.getLogger("opportunity_radar.audit")

APP_VERSION = "0.8.1"
DB_SCHEMA_REVISION = "0030_probe_task_leases"
REQUIRED_TABLES = {"alembic_version", "raw_observations", "keywords", "opportunities", "opportunity_keywords", "probe_tasks", "collection_runs", "source_health_states", "opportunity_research", "alert_rules", "alert_events", "source_preferences", "audit_logs", "seed_keywords", "opportunity_cluster_versions", "opportunity_lineage", "keyword_relation_sources", "keyword_relation_items", "alert_evaluation_queue", "email_delivery_queue", "webhook_endpoints", "webhook_delivery_queue", "worker_heartbeats", "users", "user_sessions", "api_tokens", "opportunity_score_snapshots", "daily_digests", "weekly_trend_reports", "keyword_burst_records", "tool_product_entities", "tool_product_entity_evidence", "tool_product_normalization_runs", "tool_product_occurrences", "hiring_surge_records", "cross_source_confirmations", "score_jump_records", "risk_escalation_records"}


def create_app() -> FastAPI:
    configure_logging()
    validate_runtime_settings()
    registry = build_default_registry()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            registry.close()

    app = FastAPI(title=settings.app_name, version=APP_VERSION, lifespan=lifespan)
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=settings.max_request_body_bytes)
    set_registry(registry)

    @app.middleware("http")
    async def request_context_and_audit(request: Request, call_next):
        started = time.perf_counter()
        request_id = (request.headers.get("X-Request-ID") or str(uuid.uuid4()))[:64]
        incoming_trace = request.headers.get("traceparent", "")
        trace_id = incoming_trace.split("-")[1][:32] if incoming_trace.startswith("00-") and len(incoming_trace.split("-")) >= 4 else secrets.token_hex(16)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            elapsed = max(0.0, time.perf_counter() - started)
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            metrics.observe_http(request.method.upper(), route_path, status_code, elapsed)
            logging.getLogger("opportunity_radar.http").exception(
                "request_failed",
                extra={"request_id": request_id, "trace_id": trace_id, "path": route_path, "method": request.method.upper(), "status_code": status_code, "duration_ms": round(elapsed * 1000, 2)},
            )
            raise
        finally:
            if request.method.upper() not in {"GET", "HEAD", "OPTIONS"} and request.url.path.startswith("/api/"):
                try:
                    actor = (getattr(request.state, "actor", None) or request.headers.get(settings.audit_actor_header) or "local")[:200]
                    with SessionLocal() as audit_db:
                        audit_db.add(AuditLog(
                            request_id=request_id,
                            actor=actor,
                            action=request.method.upper(),
                            resource=request.url.path[:500],
                            status_code=status_code,
                            detail={"query": sanitize_query(str(request.url.query))[:2000]},
                            created_at=utc_now(),
                        ))
                        audit_db.commit()
                except Exception:
                    # The business write may already be committed, so converting an
                    # audit sink failure into HTTP 500 would invite unsafe retries.
                    # Emit an explicit server error instead of silently pretending
                    # the audit trail was persisted.
                    LOGGER.exception("failed to persist audit log request_id=%s path=%s", request_id, request.url.path)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        elapsed = max(0.0, time.perf_counter() - started)
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        metrics.observe_http(request.method.upper(), route_path, response.status_code, elapsed)
        logging.getLogger("opportunity_radar.http").info(
            "request_completed",
            extra={"request_id": request_id, "trace_id": trace_id, "path": route_path, "method": request.method.upper(), "status_code": response.status_code, "duration_ms": round(elapsed * 1000, 3)},
        )
        return response

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(scoring_router)
    app.include_router(operations_router)
    app.include_router(research_router)
    app.include_router(router)
    attach_openapi_permissions(app)
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.app_name, "version": APP_VERSION}

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics(_auth=Depends(require_read_auth)):
        with SessionLocal() as metrics_db:
            payload = metrics.render_prometheus() + render_database_metrics(metrics_db, worker_stale_seconds=settings.worker_stale_seconds)
        return PlainTextResponse(payload, media_type="text/plain; version=0.0.4")

    @app.get("/ready")
    def ready():
        try:
            tables = set(inspect(engine).get_table_names())
        except Exception as exc:
            raise HTTPException(status_code=503, detail="database unavailable") from exc
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            raise HTTPException(status_code=503, detail={"database": "migration_required", "missing_tables": missing})
        try:
            with engine.connect() as connection:
                current_revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="database migration state unavailable") from exc
        if current_revision != DB_SCHEMA_REVISION:
            raise HTTPException(
                status_code=503,
                detail={
                    "database": "migration_required",
                    "current_revision": current_revision,
                    "required_revision": DB_SCHEMA_REVISION,
                },
            )
        return {
            "status": "ready",
            "database": "ok",
            "version": APP_VERSION,
            "schema_revision": current_revision,
        }

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()
