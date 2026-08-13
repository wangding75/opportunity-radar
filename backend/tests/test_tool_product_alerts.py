from dataclasses import replace
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import AlertEvent, ToolProductOccurrence
from app.db.session import SessionLocal
from app.main import app
from app.services.tool_product_alerts import materialize_tool_product_alerts
from app.services.tool_products import normalize_tool_product_entities

from test_tool_product_normalization import _seed_item


client = TestClient(app)


def _seed_identified_entity(db) -> None:
    first_id = _seed_item(db, source="synthetic-alert-a", title="Radar New Tool", text="MOCK tool listing", index=1)
    second_id = _seed_item(db, source="synthetic-alert-b", title="radar new tool", text="SYNTHETIC tool review", index=2)
    normalize_tool_product_entities(db, normalized_item_ids={first_id, second_id}, evaluated_at=datetime(2026, 8, 12, 6))


def test_new_tool_alert_is_evidence_backed_and_idempotent():
    with SessionLocal() as db:
        _seed_identified_entity(db)
        db.commit()
        first = materialize_tool_product_alerts(db, detected_at=datetime(2026, 8, 12, 7))
        db.commit()
        second = materialize_tool_product_alerts(db, detected_at=datetime(2026, 8, 12, 8))
        db.commit()
        event = db.scalar(select(AlertEvent).where(AlertEvent.tool_product_entity_id.is_not(None)))
        occurrence = db.scalar(select(ToolProductOccurrence).where(ToolProductOccurrence.alert_event_id == event.id))

    assert first["created"] == 1
    assert second["created"] == 0
    assert second["linked"] == 0
    assert event is not None
    assert event.opportunity_id is None
    assert event.keyword_id is None
    assert event.priority == 4
    assert "evidence_id=ev1_" in event.message
    assert "contract_version=1" in event.message
    assert occurrence is not None
    assert occurrence.alert_event_id == event.id


def test_alert_retry_after_rollback_creates_one_event_and_low_confidence_is_fail_closed():
    with SessionLocal() as db:
        _seed_identified_entity(db)
        db.commit()
        first = materialize_tool_product_alerts(db, detected_at=datetime(2026, 8, 12, 7))
        assert first["created"] == 1
        db.rollback()
        retry = materialize_tool_product_alerts(db, detected_at=datetime(2026, 8, 12, 8))
        db.commit()
        events = db.scalars(select(AlertEvent)).all()
    assert retry["created"] == 1
    assert len(events) == 1

    with SessionLocal() as db:
        item_id = _seed_item(db, source="synthetic-low-alert", title="Low Confidence Tool", text="MOCK tool", index=3)
        from app.domain.tool_product import ToolProductIdentificationPolicy
        normalize_tool_product_entities(db, normalized_item_ids={item_id}, policy=ToolProductIdentificationPolicy(min_evidence_count=1, min_confidence=0.99))
        result = materialize_tool_product_alerts(db)
        db.commit()
    assert result["created"] == 0


def test_tool_product_alert_endpoint_and_event_reader_have_rbac_boundary(monkeypatch):
    from app.core.config import settings
    import app.core.security as security

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/alerts/tool-products/evaluate")
    assert response.status_code == 401
