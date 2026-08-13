from datetime import date, datetime

from fastapi.testclient import TestClient

from app.db.models import Keyword, KeywordMention, KeywordTrendDaily, NormalizedItem, RawObservation
from app.db.session import SessionLocal
from app.domain.keyword_burst import KeywordBurstPolicy
from app.main import app
from app.services.keyword_burst_alerts import materialize_keyword_burst_alerts


client = TestClient(app)
WINDOW_END = date(2026, 8, 12)


def _seed_burst(*, with_evidence: bool) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical=f"burst-evidence-{with_evidence}", display_name="Burst Evidence", status="ACTIVE")
        db.add(keyword)
        db.flush()
        points = [(date(2026, 8, 3 + offset), 1) for offset in range(6)] + [(date(2026, 8, 9), 4), (date(2026, 8, 10), 5), (date(2026, 8, 11), 6)]
        for index, (day, count) in enumerate(points):
            db.add(KeywordTrendDaily(keyword_id=keyword.id, day=day, observation_count=count, source_count=2))
            if with_evidence:
                raw = RawObservation(
                    source_id="synthetic-burst",
                    external_id=f"burst-{with_evidence}-{index}",
                    query="synthetic burst",
                    item_type="CONTENT",
                    title=f"SYNTHETIC burst evidence {index}",
                    text="MOCK keyword burst evidence",
                    source_url="https://synthetic.invalid/burst",
                    observed_at=datetime.combine(day, datetime.min.time()),
                    acquisition_method="MANUAL_IMPORT",
                    evidence_quality="E",
                    acquisition_risk="R2",
                    content_hash=f"{index + 1:064x}",
                    raw_payload={"data_class": "SYNTHETIC"},
                )
                db.add(raw)
                db.flush()
                item = NormalizedItem(
                    raw_observation_id=raw.id,
                    canonical_key=f"burst-item-{with_evidence}-{index}",
                    source_id=raw.source_id,
                    query=raw.query,
                    item_type=raw.item_type,
                    title=raw.title,
                    text=raw.text,
                    source_url=raw.source_url,
                    observed_at=raw.observed_at,
                )
                db.add(item)
                db.flush()
                db.add(KeywordMention(keyword_id=keyword.id, normalized_item_id=item.id, source_id=raw.source_id, observed_at=raw.observed_at))
        db.commit()
        return keyword.id


def _policy() -> KeywordBurstPolicy:
    return KeywordBurstPolicy(current_window_days=3, baseline_window_days=6, min_current_observations=6, min_absolute_delta=4, min_growth_rate=0.5, min_z_score=2.0)


def test_burst_alert_persists_evidence_explanation_and_idempotent_event():
    keyword_id = _seed_burst(with_evidence=True)
    with SessionLocal() as db:
        first = materialize_keyword_burst_alerts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=_policy())
        db.commit()
        second = materialize_keyword_burst_alerts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=_policy())
        db.commit()

    assert first == {"rule": "KEYWORD_BURST", "evaluated": 1, "anomalous": 1, "created": 1, "duplicates": 0, "evidence_missing": 0}
    assert second["created"] == 0 and second["duplicates"] == 1
    events = client.get("/api/v1/alerts/events", params={"limit": 100}).json()
    event = next(row for row in events if row["keyword_id"] == keyword_id)
    assert event["opportunity_id"] is None
    assert event["priority"] == 5
    assert "evidence_ids=ev1_" in event["message"]

    records = client.get("/api/v1/alerts/keyword-burst/records", params={"keyword_id": keyword_id}).json()
    assert len(records) == 1
    assert records[0]["status"] == "ANOMALOUS"
    assert records[0]["evidence"]
    assert records[0]["explanation"]["z_score"] >= 2
    assert len(records[0]["explanation"]["evidence_ids"]) == len(records[0]["evidence"])

    acknowledged = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert acknowledged.status_code == 200


def test_burst_alert_fails_closed_when_daily_materialization_has_no_raw_evidence():
    keyword_id = _seed_burst(with_evidence=False)
    with SessionLocal() as db:
        result = materialize_keyword_burst_alerts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=_policy())
        db.commit()

    assert result["anomalous"] == 1
    assert result["created"] == 0
    assert result["evidence_missing"] == 1
    assert not [row for row in client.get("/api/v1/alerts/events", params={"limit": 100}).json() if row["keyword_id"] == keyword_id]
    records = client.get("/api/v1/alerts/keyword-burst/records", params={"keyword_id": keyword_id}).json()
    assert records[0]["status"] == "REJECTED_NO_EVIDENCE"
    assert records[0]["explanation"]["fail_closed_reason"]


def test_burst_evaluation_endpoint_requires_admin_in_rbac(monkeypatch):
    from dataclasses import replace

    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/alerts/keyword-burst/evaluate")
    assert response.status_code == 401
