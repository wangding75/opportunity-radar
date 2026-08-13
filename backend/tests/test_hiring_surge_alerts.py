from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import AlertEvent, HiringSurgeRecord, Keyword, KeywordMention, NormalizedItem, Opportunity, OpportunityKeyword, RawObservation
from app.db.session import SessionLocal
from app.main import app
from app.services.hiring_surge_alerts import materialize_hiring_surge_alerts


client = TestClient(app)
WINDOW_END = "2026-08-12"


def _seed_job(db, keyword: Keyword, *, day: date, title: str, company: str, source: str, index: int) -> None:
    observed_at = datetime.combine(day, datetime.min.time())
    raw = RawObservation(
        source_id=source,
        external_id=f"synthetic-alert-job-{index}",
        query=keyword.display_name,
        item_type="JOB",
        title=title,
        text=f"MOCK company: {company} location: Remote hiring",
        source_url=f"https://synthetic.invalid/jobs/{index}",
        observed_at=observed_at,
        acquisition_method="MANUAL_IMPORT",
        evidence_quality="E",
        acquisition_risk="R2",
        content_hash=f"{index:064x}",
        raw_payload={"data_class": "SYNTHETIC", "company": company, "location": "Remote"},
    )
    db.add(raw)
    db.flush()
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=f"synthetic-alert-job-item-{index}",
        source_id=source,
        query=keyword.display_name,
        item_type="JOB",
        title=title,
        text=raw.text,
        source_url=raw.source_url,
        observed_at=observed_at,
    )
    db.add(item)
    db.flush()
    db.add(KeywordMention(keyword_id=keyword.id, normalized_item_id=item.id, source_id=source, observed_at=observed_at))


def _seed_surge() -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-hiring-alert", display_name="Synthetic Hiring Alert", status="ACTIVE")
        db.add(keyword)
        db.flush()
        index = 1
        for offset in range(6):
            _seed_job(db, keyword, day=date(2026, 8, 3 + offset), title="Baseline Engineer", company="Baseline Co", source="synthetic-baseline", index=index)
            index += 1
        for day_offset, company in ((9, "Acme A"), (10, "Acme B"), (11, "Acme C")):
            for role_offset in range(4):
                _seed_job(db, keyword, day=date(2026, 8, day_offset), title=f"Growth Engineer {role_offset}", company=company, source="synthetic-jobs-a", index=index)
                index += 1
            if day_offset == 9:
                _seed_job(db, keyword, day=date(2026, 8, day_offset), title="Growth Engineer 0", company=company, source="synthetic-jobs-b", index=index)
                index += 1
        db.commit()
        return keyword.id


def _link_opportunity(keyword_id: int) -> int:
    with SessionLocal() as db:
        opportunity = Opportunity(
            opportunity_key=f"synthetic-hiring-opportunity-{keyword_id}",
            keyword_id=keyword_id,
            title="Synthetic hiring opportunity",
            stage="VALIDATED",
            score=88.0,
            summary="MOCK opportunity linked to a synthetic hiring signal",
        )
        db.add(opportunity)
        db.flush()
        db.add(OpportunityKeyword(opportunity_id=opportunity.id, keyword_id=keyword_id, role="PRIMARY", weight=1.0))
        db.commit()
        return opportunity.id


def test_hiring_surge_alert_persists_evidence_links_opportunity_and_is_idempotent():
    keyword_id = _seed_surge()
    opportunity_id = _link_opportunity(keyword_id)

    with SessionLocal() as db:
        first = materialize_hiring_surge_alerts(db, keyword_ids={keyword_id}, window_end=date.fromisoformat(WINDOW_END))
        db.commit()
        second = materialize_hiring_surge_alerts(db, keyword_ids={keyword_id}, window_end=date.fromisoformat(WINDOW_END))
        db.commit()

    assert first["evaluated"] == 1
    assert first["surges"] == 1
    assert first["created"] == 1
    assert first["evidence_missing"] == 0
    assert first["opportunities_linked"] == 1
    assert second["created"] == 0
    assert second["duplicates"] == 1

    with SessionLocal() as db:
        record = db.scalar(select(HiringSurgeRecord).where(HiringSurgeRecord.keyword_id == keyword_id))
        event = db.scalar(select(AlertEvent).where(AlertEvent.keyword_id == keyword_id))
        assert record is not None
        assert record.status == "SURGE"
        assert record.current_start == date(2026, 8, 5)
        assert record.current_end == date(2026, 8, 12)
        assert record.baseline_end == record.current_start
        assert record.opportunity_id == opportunity_id
        assert record.alert_event_id == event.id
        assert record.evidence
        assert record.evidence_ids
        assert record.explanation["alert_event_id"] == event.id
        assert event.opportunity_id == opportunity_id
        assert event.priority == 4
        assert "detection_signature=" in event.message
        assert "evidence_ids=ev1_" in event.message
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.keyword_id == keyword_id)) == 1

    rows = client.get("/api/v1/alerts/hiring/records", params={"keyword_id": keyword_id}).json()
    assert len(rows) == 1
    assert rows[0]["status"] == "SURGE"
    assert rows[0]["opportunity_id"] == opportunity_id
    assert rows[0]["evidence"]


def test_hiring_surge_alert_fails_closed_without_resolvable_evidence(monkeypatch):
    keyword_id = _seed_surge()

    import app.services.hiring_surge_alerts as alerts

    monkeypatch.setattr(alerts, "_evidence", lambda db, detection: [])
    with SessionLocal() as db:
        result = materialize_hiring_surge_alerts(db, keyword_ids={keyword_id}, window_end=date.fromisoformat(WINDOW_END))
        db.commit()

    assert result["surges"] == 1
    assert result["created"] == 0
    assert result["evidence_missing"] == 1
    with SessionLocal() as db:
        record = db.scalar(select(HiringSurgeRecord).where(HiringSurgeRecord.keyword_id == keyword_id))
        assert record.status == "REJECTED_NO_EVIDENCE"
        assert record.alert_event_id is None
        assert record.explanation["fail_closed_reason"]
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.keyword_id == keyword_id)) == 0


def test_hiring_surge_alert_rollback_can_retry_without_duplicate_event():
    keyword_id = _seed_surge()
    with SessionLocal() as db:
        first = materialize_hiring_surge_alerts(db, keyword_ids={keyword_id}, window_end=date.fromisoformat(WINDOW_END))
        assert first["created"] == 1
        db.rollback()
        retry = materialize_hiring_surge_alerts(db, keyword_ids={keyword_id}, window_end=date.fromisoformat(WINDOW_END))
        db.commit()

    assert retry["created"] == 1
    with SessionLocal() as db:
        assert db.scalar(select(func.count(HiringSurgeRecord.id)).where(HiringSurgeRecord.keyword_id == keyword_id)) == 1
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.keyword_id == keyword_id)) == 1


def test_hiring_surge_alert_empty_evaluation_is_a_noop():
    with SessionLocal() as db:
        result = materialize_hiring_surge_alerts(db, keyword_ids=set())
        db.commit()

    assert result == {
        "rule": "HIRING_SURGE",
        "evaluated": 0,
        "surges": 0,
        "created": 0,
        "duplicates": 0,
        "evidence_missing": 0,
        "opportunities_linked": 0,
    }


def test_hiring_surge_evaluation_endpoint_requires_admin_in_rbac(monkeypatch):
    from dataclasses import replace

    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/alerts/hiring/evaluate")
    assert response.status_code == 401
