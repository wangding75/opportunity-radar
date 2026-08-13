from datetime import date

from fastapi.testclient import TestClient

from app.db.models import Keyword, KeywordBurstRecord, KeywordTrendDaily
from app.db.session import SessionLocal
from app.main import app
from app.services.keyword_burst_replay import replay_keyword_bursts


client = TestClient(app)


def _seed_replay_keyword() -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical="replay-burst", display_name="Replay Burst", status="ACTIVE")
        db.add(keyword)
        db.flush()
        for day_offset in range(42):
            day = date(2026, 7, 1).fromordinal(date(2026, 7, 1).toordinal() + day_offset)
            count = 5 if date(2026, 7, 20) <= day < date(2026, 7, 27) else (1 if day < date(2026, 7, 20) else 0)
            db.add(KeywordTrendDaily(keyword_id=keyword.id, day=day, observation_count=count, source_count=2 if count else 0))
        db.commit()
        return keyword.id


def test_replay_is_read_only_bounded_and_stable():
    keyword_id = _seed_replay_keyword()
    with SessionLocal() as db:
        first = replay_keyword_bursts(db, keyword_id=keyword_id, start_window_end=date(2026, 7, 27), end_window_end=date(2026, 8, 10))
        second = replay_keyword_bursts(db, keyword_id=keyword_id, start_window_end=date(2026, 7, 27), end_window_end=date(2026, 8, 10))
        assert db.query(KeywordTrendDaily).count() == 42
        assert db.query(KeywordBurstRecord).count() == 0

    assert first["windows"] == 3
    assert first["anomalous_windows"] >= 1
    assert first["input_signatures"] == second["input_signatures"]
    assert first["results"] == second["results"]


def test_replay_rejects_unbounded_range_and_api_requires_admin(monkeypatch):
    keyword_id = _seed_replay_keyword()
    with SessionLocal() as db:
        try:
            replay_keyword_bursts(db, keyword_id=keyword_id, start_window_end=date(2026, 1, 1), end_window_end=date(2027, 1, 1))
        except ValueError as exc:
            assert "exceeds" in str(exc)
        else:
            raise AssertionError("unbounded replay must fail closed")

    from dataclasses import replace
    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/alerts/keyword-burst/replay", params={"keyword_id": keyword_id, "start_window_end": "2026-07-27", "end_window_end": "2026-08-10"})
    assert response.status_code == 401
