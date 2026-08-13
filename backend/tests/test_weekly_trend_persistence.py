from datetime import date

from fastapi.testclient import TestClient

from app.db.models import Keyword, KeywordTrendDaily
from app.db.session import SessionLocal
from app.domain.weekly_trends import WeeklyTrendStatus
from app.main import app
from app.services.weekly_trend_persistence import get_weekly_trend_report, save_weekly_trend_report
from app.services.weekly_trends import aggregate_weekly_trends


def test_weekly_trend_persistence_is_idempotent_and_round_trips_explanations():
    with SessionLocal() as db:
        keyword = Keyword(
            canonical="persisted trend",
            display_name="Persisted trend",
            status="ACTIVE",
            observation_count=8,
            source_count=2,
        )
        db.add(keyword)
        db.flush()
        db.add_all([
            KeywordTrendDaily(keyword_id=keyword.id, day=date(2026, 7, 27), observation_count=1, source_count=1),
            KeywordTrendDaily(keyword_id=keyword.id, day=date(2026, 8, 3), observation_count=4, source_count=2),
        ])
        db.flush()
        report = aggregate_weekly_trends(db, anchor_date=date(2026, 8, 12))
        first = save_weekly_trend_report(db, report)
        second = save_weekly_trend_report(db, report)
        db.commit()
        loaded = get_weekly_trend_report(db, week_start=date(2026, 8, 3))
    assert first.id == second.id
    assert loaded.status == WeeklyTrendStatus.READY
    assert loaded.model_dump(mode="json") == report.model_dump(mode="json")
    assert first.explanation["status"] == "READY"
    assert first.explanation["items"][0]["selection_reasons"]
    assert first.explanation["items"][0]["trend_signature"] == loaded.items[0].trend_signature


def test_weekly_trend_query_and_generation_api_round_trip():
    client = TestClient(app)
    missing = client.get("/api/v1/trends/weekly/2026-08-03")
    assert missing.status_code == 404
    generated = client.post("/api/v1/trends/weekly/generate?anchor_date=2026-08-12")
    assert generated.status_code == 200
    assert generated.json()["status"] == "EMPTY"
    fetched = client.get("/api/v1/trends/weekly?week_start=2026-08-03")
    assert fetched.status_code == 200
    assert fetched.json()["input_signature"] == generated.json()["input_signature"]
    latest = client.get("/api/v1/trends/weekly")
    assert latest.status_code == 200
    assert latest.json()["week_start"] == "2026-08-03"


def test_weekly_trend_generation_requires_admin_in_rbac(monkeypatch):
    from dataclasses import replace

    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = TestClient(app).post("/api/v1/trends/weekly/generate?anchor_date=2026-08-12")
    assert response.status_code == 401
