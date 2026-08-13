from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import settings, validate_runtime_settings
from app.core.time import utc_now
from app.db.models import (
    Keyword,
    Opportunity,
    OpportunityKeyword,
    OpportunityLineage,
    OpportunityScoreSnapshot,
    ProbeTask,
    UserSession,
)
from app.db.session import SessionLocal
from app.domain.schemas import ImportRecord, ImportRequest, MAX_IMPORT_REQUEST_BYTES
from app.services.auth import create_session, create_user, validate_csrf
from app.services.opportunities import _match_components
from app.services.probes import PROBE_CLAIM_LEASE_MINUTES, _claim_due_task
from app.services.scoring import SCORING_MODEL_VERSION, backtest_summary


def _keyword(db, name: str, score: float = 50.0) -> Keyword:
    now = utc_now()
    row = Keyword(
        canonical=name,
        display_name=name,
        status="ACTIVE",
        first_seen_at=now,
        last_seen_at=now,
        observation_count=3,
        source_count=2,
        score=score,
    )
    db.add(row)
    db.flush()
    return row


def test_split_identity_follows_strongest_overlap_not_component_order():
    with SessionLocal() as db:
        k1, k2, k3, k4 = [_keyword(db, f"stable-split-{idx}", 100 - idx) for idx in range(4)]
        parent = Opportunity(opportunity_key="opp:stable-parent", keyword_id=k1.id, title="parent", stage="DISCOVERY")
        db.add(parent)
        db.flush()
        for index, kw in enumerate((k1, k2, k3, k4)):
            db.add(OpportunityKeyword(opportunity_id=parent.id, keyword_id=kw.id, role="PRIMARY" if index == 0 else "RELATED", weight=kw.score))
        db.flush()

        assigned = _match_components(
            db,
            [[k1], [k2, k3, k4]],  # weaker fragment intentionally comes first
            [parent],
            {parent.id: {k1.id, k2.id, k3.id, k4.id}},
            now=utc_now(),
        )
        assert assigned[0][1].id != parent.id
        assert assigned[1][1].id == parent.id
        db.flush()
        lineage = db.scalars(select(OpportunityLineage)).all()
        assert any(row.parent_opportunity_id == parent.id and row.child_opportunity_id == assigned[0][1].id for row in lineage)


def test_backtest_carries_forward_state_and_excludes_immature_signals():
    now = utc_now()
    with SessionLocal() as db:
        kw1 = _keyword(db, "backtest-persist")
        kw2 = _keyword(db, "backtest-drop")
        kw3 = _keyword(db, "backtest-recent")
        opportunities = []
        for idx, kw in enumerate((kw1, kw2, kw3), 1):
            opp = Opportunity(opportunity_key=f"opp:bt-{idx}", keyword_id=kw.id, title=f"bt-{idx}", stage="DISCOVERY")
            db.add(opp); db.flush(); opportunities.append(opp)
        # No later change means the threshold state persisted through day 30.
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunities[0].id, model_version=SCORING_MODEL_VERSION, input_signature="a"*64, score=70, risk_score=0, stage="DISCOVERY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=45)))
        # This signal drops before its 30-day horizon.
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunities[1].id, model_version=SCORING_MODEL_VERSION, input_signature="b"*64, score=75, risk_score=0, stage="DISCOVERY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=50)))
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunities[1].id, model_version=SCORING_MODEL_VERSION, input_signature="c"*64, score=40, risk_score=0, stage="DISCOVERY", evidence_count=3, breakdown={}, calculated_at=now-timedelta(days=35)))
        # Recent crossing must be reported as immature, never as a failed signal.
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunities[2].id, model_version=SCORING_MODEL_VERSION, input_signature="d"*64, score=80, risk_score=0, stage="DISCOVERY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=5)))
        db.commit()
        result = backtest_summary(db, lookback_days=90, threshold=60)
        assert result["candidate_signals"] == 2
        assert result["persisted_signals"] == 1
        assert result["immature_signals"] == 1
        assert result["persistence_rate"] == 0.5


def test_probe_claim_lease_outlives_stale_run_threshold():
    assert PROBE_CLAIM_LEASE_MINUTES > 30
    with SessionLocal() as db:
        now = utc_now()
        task = ProbeTask(source_id="lease-source", query="lease", intent="BASE", priority=1, interval_minutes=60, active=True, next_run_at=now-timedelta(seconds=1), created_at=now, updated_at=now)
        db.add(task); db.commit()
        assert _claim_due_task(db, task.id, now=now)
        assert not _claim_due_task(db, task.id, now=now + timedelta(minutes=20))


def test_analysis_timeout_is_bounded_below_stale_window():
    with pytest.raises(ValueError, match="ANALYSIS_HTTP_TIMEOUT_SECONDS"):
        validate_runtime_settings(replace(settings, analysis_http_timeout_seconds=301))
    validate_runtime_settings(replace(settings, analysis_http_timeout_seconds=300))


def test_expired_session_csrf_is_rejected():
    with SessionLocal() as db:
        user = create_user(db, "csrf-expired", "CsrfExpiredPassword-2026!", role="RESEARCHER")
        _, csrf, session = create_session(db, user, ttl_hours=1)
        session.expires_at = utc_now() - timedelta(seconds=1)
        db.commit()
        assert validate_csrf(db, session.id, csrf) is False


def test_import_payload_size_limits_prevent_storage_amplification():
    with pytest.raises(ValidationError, match="observation exceeds"):
        ImportRecord(source_id="manual-large", query="large", payload={"blob": "x" * (600 * 1024)})

    # Aggregate request limit is enforced even when each individual record is valid.
    record = ImportRecord(source_id="manual-many", query="many", text="x" * 200_000)
    count = (MAX_IMPORT_REQUEST_BYTES // 200_000) + 2
    with pytest.raises(ValidationError, match="import request exceeds"):
        ImportRequest(records=[record.model_copy() for _ in range(count)])


def test_researcher_cannot_inject_manual_or_instrumented_evidence(monkeypatch):
    from fastapi.testclient import TestClient
    import app.core.security as security
    from app.main import app
    from app.services.auth import create_api_token

    with SessionLocal() as db:
        user = create_user(db, "no-poison", "NoPoisonPassword-2026!", role="RESEARCHER")
        token, _ = create_api_token(db, user, name="research", scopes=["read", "write"])
        db.commit()

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    manual = client.post(
        "/api/v1/import",
        headers=headers,
        json={"records": [{"source_id": "manual-researcher", "query": "poison", "title": "poison"}]},
    )
    instrumented = client.post(
        "/api/v1/instrumented-app/observations",
        headers=headers,
        json=[{"source_id": "app-researcher", "query": "poison", "app_package": "example.app", "title": "poison"}],
    )
    assert manual.status_code == 403
    assert instrumented.status_code == 403


def test_payload_depth_limit_prevents_recursive_sanitizer_exhaustion():
    payload: dict = {"leaf": "ok"}
    for _ in range(40):
        payload = {"nested": payload}
    with pytest.raises(ValidationError, match="depth limit"):
        ImportRecord(source_id="manual-deep", query="deep", payload=payload)


def test_request_body_limit_rejects_chunked_body_without_content_length():
    import asyncio
    from app.core.request_limits import RequestBodyLimitMiddleware

    reached = {"app": False}
    sent: list[dict] = []
    messages = iter([
        {"type": "http.request", "body": b"123456", "more_body": True},
        {"type": "http.request", "body": b"789012", "more_body": False},
    ])

    async def downstream(_scope, receive, send):
        reached["app"] = True
        while True:
            message = await receive()
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    middleware = RequestBodyLimitMiddleware(downstream, max_bytes=10)
    asyncio.run(middleware({"type": "http", "method": "POST", "headers": []}, receive, send))
    assert reached["app"] is False
    assert sent[0]["status"] == 413


def test_opportunity_cursor_page_preserves_research_filters():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.models import OpportunityResearch

    with SessionLocal() as db:
        k1 = _keyword(db, "page-starred-1")
        k2 = _keyword(db, "page-starred-2")
        o1 = Opportunity(opportunity_key="opp:page-1", keyword_id=k1.id, title="page one", stage="DISCOVERY", score=80, first_seen_at=utc_now(), last_seen_at=utc_now(), updated_at=utc_now())
        o2 = Opportunity(opportunity_key="opp:page-2", keyword_id=k2.id, title="page two", stage="DISCOVERY", score=70, first_seen_at=utc_now(), last_seen_at=utc_now(), updated_at=utc_now())
        db.add_all([o1, o2]); db.flush()
        db.add(OpportunityResearch(opportunity_id=o1.id, status="TRACKING", starred=True, priority=4, tags=[], notes="", created_at=utc_now(), updated_at=utc_now()))
        db.commit()

    client = TestClient(app)
    response = client.get("/api/v1/opportunities/page?research_status=TRACKING&starred=true&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "page one"
    assert data["items"][0]["research"]["starred"] is True


def test_http_analysis_timeout_must_fit_worker_heartbeat_window():
    with pytest.raises(ValueError, match="WORKER_STALE_SECONDS"):
        validate_runtime_settings(replace(settings, analysis_provider="http", analysis_http_endpoint="http://analysis.local", analysis_http_timeout_seconds=170, worker_stale_seconds=180))
    validate_runtime_settings(replace(settings, analysis_provider="http", analysis_http_endpoint="http://analysis.local", analysis_http_timeout_seconds=100, worker_stale_seconds=180))


def test_researcher_cannot_read_admin_operations_and_source_errors_are_redacted(monkeypatch):
    from fastapi.testclient import TestClient
    import app.core.security as security
    from app.main import app
    from app.services.auth import create_api_token
    from app.services.source_health import record_failure

    with SessionLocal() as db:
        user = create_user(db, "ops-boundary", "OpsBoundaryPassword-2026!", role="RESEARCHER")
        token, _ = create_api_token(db, user, name="ops-boundary", scopes=["read", "write"])
        record_failure(db, "github", "internal connector detail that should not reach researcher")
        db.commit()

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/probes/tasks", headers=headers).status_code == 403
    assert client.get("/api/v1/collection-runs", headers=headers).status_code == 403
    health = client.get("/api/v1/sources/health", headers=headers)
    assert health.status_code == 200
    github = next(row for row in health.json() if row["source_id"] == "github")
    assert github["last_error"] is None


def test_compose_keeps_postgres_password_out_of_database_url():
    from pathlib import Path
    import yaml

    compose = yaml.safe_load((Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text())
    for service_name in ("migrate", "api", "worker-collection", "maintenance"):
        env = compose["services"][service_name]["environment"]
        assert "${POSTGRES_PASSWORD}@" not in env["DATABASE_URL"]
        assert env["DATABASE_URL"] == "postgresql+psycopg://opportunity_radar@postgres:5432/opportunity_radar"
        assert env["PGPASSWORD"] == "${POSTGRES_PASSWORD}"


def test_production_external_analysis_requires_https():
    base = replace(
        settings,
        app_env="production",
        auth_mode="rbac",
        allow_legacy_api_key=False,
        database_url="postgresql+psycopg://user@db/radar",
        analysis_provider="http",
        analysis_http_endpoint="http://analysis.internal/v1",
        analysis_http_timeout_seconds=20,
        worker_stale_seconds=180,
    )
    with pytest.raises(ValueError, match="HTTPS ANALYSIS_HTTP_ENDPOINT"):
        validate_runtime_settings(base)
    validate_runtime_settings(replace(base, analysis_http_endpoint="https://analysis.example/v1"))


def test_observation_payload_rejects_non_json_values_before_ingestion():
    with pytest.raises(ValidationError, match="JSON-serializable"):
        ImportRecord(source_id="manual-json-contract", query="json", payload={"when": utc_now()})


def test_long_maintenance_sleep_refreshes_idle_heartbeat(monkeypatch):
    import app.worker as worker
    sleeps: list[int] = []
    beats: list[tuple[str, str, str]] = []
    monkeypatch.setattr(worker.time, "sleep", lambda seconds: sleeps.append(int(seconds)))
    monkeypatch.setattr(worker, "_touch_heartbeat", lambda worker_id, mode, status="RUNNING": beats.append((worker_id, mode, status)))
    monkeypatch.setattr(worker, "settings", replace(settings, maintenance_worker_stale_seconds=1800))
    worker._sleep_with_heartbeat(2000, "maintenance-test", "maintenance")
    assert max(sleeps) <= 900
    assert sum(sleeps) == 2000
    assert len(beats) >= 2
    assert all(status == "IDLE" for _worker_id, _mode, status in beats)


def test_compose_runs_periodic_maintenance_by_default():
    from pathlib import Path
    import yaml
    compose = yaml.safe_load((Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text())
    service = compose["services"]["worker-maintenance"]
    assert "profiles" not in service
    command = service["command"]
    assert command[command.index("--mode") + 1] == "maintenance"
    assert "--once" not in command
    assert "--interval" in command


def test_backtest_uses_exact_pre_window_state_not_fixed_warmup():
    now = utc_now()
    with SessionLocal() as db:
        kw = _keyword(db, "backtest-prewindow-state")
        opp = Opportunity(opportunity_key="opp:bt-prewindow", keyword_id=kw.id, title="bt-prewindow", stage="DISCOVERY")
        db.add(opp); db.flush()
        # The opportunity was already above threshold long before the 90-day window.
        db.add(OpportunityScoreSnapshot(opportunity_id=opp.id, model_version=SCORING_MODEL_VERSION, input_signature="e"*64, score=65, risk_score=0, stage="DISCOVERY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=200)))
        # A changed high score inside the lookback must not be counted as a fresh crossing.
        db.add(OpportunityScoreSnapshot(opportunity_id=opp.id, model_version=SCORING_MODEL_VERSION, input_signature="f"*64, score=80, risk_score=0, stage="DISCOVERY", evidence_count=3, breakdown={}, calculated_at=now-timedelta(days=60)))
        db.commit()
        result = backtest_summary(db, lookback_days=90, threshold=60)
        assert result["candidate_signals"] == 0
        assert result["immature_signals"] == 0


def test_instrumented_sanitizer_strips_url_userinfo_and_api_keys():
    from app.services.sanitizer import sanitize_instrumented
    from app.domain.schemas import CollectedRecord
    record = CollectedRecord(
        title="contact a@example.com",
        text="phone 13800138000",
        url="https://user:secret@example.com/path?api_key=topsecret&safe=1",
        payload={"api_key": "topsecret", "accessToken": "camel-secret", "deviceId": "device-secret", "nested": {"apikey": "also-secret", "safe": "ok"}},
    )
    clean = sanitize_instrumented(record)
    assert clean.url == "https://example.com/path?safe=1"
    assert clean.payload == {"nested": {"safe": "ok"}}
    assert "a@example.com" not in clean.title
    assert "13800138000" not in clean.text


def test_researcher_cannot_force_global_alert_evaluation(monkeypatch):
    from fastapi.testclient import TestClient
    import app.core.security as security
    from app.main import app
    from app.services.auth import create_api_token

    with SessionLocal() as db:
        user = create_user(db, "alert-operator-boundary", "AlertBoundaryPassword-2026!", role="RESEARCHER")
        token, _ = create_api_token(db, user, name="alert-boundary", scopes=["read", "write"])
        db.commit()
    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/alerts/evaluate", headers=headers).status_code == 403
    assert client.post("/api/v1/alerts/run-pending", headers=headers).status_code == 403
