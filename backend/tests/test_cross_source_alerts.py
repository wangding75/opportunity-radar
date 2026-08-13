import hashlib
from datetime import datetime
from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import AlertEvent, CrossSourceConfirmationRecord, Keyword, NormalizedItem, Opportunity, OpportunityEvidence, RawObservation
from app.db.session import SessionLocal
from app.main import app
from app.services.cross_source_confirmations import materialize_cross_source_confirmations
from app.services.cross_source_alerts import materialize_cross_source_alerts


client = TestClient(app)
NOW = datetime(2026, 8, 12, 12)


def _seed_opportunity(*, same_endpoint: bool = False, with_evidence: bool = True) -> int:
    with SessionLocal() as db:
        suffix = f"{same_endpoint}-{with_evidence}"
        keyword = Keyword(canonical=f"synthetic-cross-alert-{suffix}", display_name="SYNTHETIC Cross Alert", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key=f"synthetic-cross-alert-{suffix}",
            keyword_id=keyword.id,
            title="SYNTHETIC cross-source alert opportunity",
            stage="VALIDATED",
            score=84.0,
        )
        db.add(opportunity)
        db.flush()
        if with_evidence:
            rows = [
                ("synthetic-alert-a", "Claim A", "Independent claim A", "https://a.synthetic.invalid/1", "a"),
                ("synthetic-alert-b", "Claim B", "Independent claim B", "https://a.synthetic.invalid/2" if same_endpoint else "https://b.synthetic.invalid/2", "b"),
                ("synthetic-alert-b", "Claim A", "Independent claim A", "https://a.synthetic.invalid/3" if same_endpoint else "https://b.synthetic.invalid/3", "c"),
            ]
            for source, title, text, url, marker in rows:
                raw = RawObservation(
                    source_id=source,
                    external_id=f"synthetic-alert-{suffix}-{marker}",
                    query="synthetic cross alert",
                    item_type="CONTENT",
                    title=title,
                    text=text,
                    source_url=url,
                    observed_at=NOW,
                    acquisition_method="MANUAL_IMPORT",
                    evidence_quality="E",
                    acquisition_risk="R2",
                    content_hash=hashlib.sha256(f"{suffix}-{marker}".encode()).hexdigest(),
                    raw_payload={"data_class": "SYNTHETIC"},
                )
                db.add(raw)
                db.flush()
                item = NormalizedItem(
                    raw_observation_id=raw.id,
                    canonical_key=hashlib.sha256(f"item-{suffix}-{marker}".encode()).hexdigest(),
                    source_id=source,
                    query=raw.query,
                    item_type=raw.item_type,
                    title=title,
                    text=text,
                    source_url=url,
                    observed_at=NOW,
                )
                db.add(item)
                db.flush()
                db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", observed_at=NOW))
        db.commit()
        return opportunity.id


def test_cross_source_api_scores_confirmed_record_delivers_and_deduplicates_alert():
    opportunity_id = _seed_opportunity()
    first = client.post("/api/v1/alerts/cross-source/evaluate", params={"opportunity_id": opportunity_id})
    assert first.status_code == 200
    payload = first.json()
    assert payload["confirmation"]["confirmed"] == 1
    assert payload["alerts"]["eligible"] == 1
    assert payload["alerts"]["created"] == 1

    second = client.post("/api/v1/alerts/cross-source/evaluate", params={"opportunity_id": opportunity_id})
    assert second.status_code == 200
    assert second.json()["confirmation"]["duplicates"] == 1
    assert second.json()["alerts"]["duplicates"] == 1
    assert second.json()["alerts"]["created"] == 0

    with SessionLocal() as db:
        record = db.scalar(select(CrossSourceConfirmationRecord).where(CrossSourceConfirmationRecord.opportunity_id == opportunity_id))
        event = db.scalar(select(AlertEvent).where(AlertEvent.opportunity_id == opportunity_id))
        assert record is not None
        assert record.score == 81.0
        assert record.risk_score == 5.0
        assert record.alert_event_id == event.id
        assert event.priority == 5
        assert "score_input_signature=" in event.message
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.opportunity_id == opportunity_id)) == 1

    rows = client.get("/api/v1/alerts/cross-source/records", params={"opportunity_id": opportunity_id}).json()
    assert rows[0]["score_algorithm_version"] == "cross-source-score-v1"
    assert rows[0]["alert_event_id"] is not None
    event = client.get("/api/v1/alerts/events", params={"limit": 100}).json()[0]
    acknowledged = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert acknowledged.status_code == 200


def test_unconfirmed_or_empty_records_are_suppressed_without_alert_event():
    same_endpoint_id = _seed_opportunity(same_endpoint=True)
    empty_id = _seed_opportunity(with_evidence=False)
    with SessionLocal() as db:
        confirmation = materialize_cross_source_confirmations(db, opportunity_ids={same_endpoint_id, empty_id}, evaluated_at=NOW)
        alerts = materialize_cross_source_alerts(db, opportunity_ids={same_endpoint_id, empty_id})
        db.commit()

    assert confirmation["confirmed"] == 0
    assert confirmation["insufficient"] == 1
    assert confirmation["no_evidence"] == 1
    assert alerts["created"] == 0
    assert alerts["suppressed"] == 2
    with SessionLocal() as db:
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.opportunity_id.in_([same_endpoint_id, empty_id]))) == 0


def test_cross_source_evaluation_endpoint_requires_admin_in_rbac(monkeypatch):
    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/alerts/cross-source/evaluate")
    assert response.status_code == 401
