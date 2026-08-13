from datetime import datetime
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import ToolProductOccurrence
from app.db.session import SessionLocal
from app.main import app
from app.domain.tool_product import ToolProductIdentificationPolicy
from app.services.tool_product_occurrences import (
    DUPLICATE,
    FIRST_SEEN,
    materialize_tool_product_occurrences,
    list_tool_product_occurrences,
)
from app.services.tool_products import normalize_tool_product_entities

from test_tool_product_normalization import _seed_item


client = TestClient(app)


def test_first_seen_and_duplicate_classification_is_stable_and_traceable():
    with SessionLocal() as db:
        first_id = _seed_item(db, source="synthetic-occurrence-a", title="Radar Tool", text="MOCK tool", index=1)
        second_id = _seed_item(db, source="synthetic-occurrence-b", title="radar tool", text="SYNTHETIC tool", index=2)
        normalize_tool_product_entities(db, normalized_item_ids={first_id, second_id}, evaluated_at=datetime(2026, 8, 12, 6))
        first = materialize_tool_product_occurrences(db, detected_at=datetime(2026, 8, 12, 7))
        db.commit()

        repeat = materialize_tool_product_occurrences(db, detected_at=datetime(2026, 8, 12, 8))
        rows = list_tool_product_occurrences(db)
        db.commit()

    assert first["first_seen"] == 1
    assert first["duplicates"] == 1
    assert repeat["already_materialized"] == 2
    assert [row["classification"] for row in rows] == [FIRST_SEEN, DUPLICATE]
    assert rows[0]["observed_at"] < rows[1]["observed_at"]
    assert rows[0]["evidence_id"].startswith("ev1_")


def test_empty_occurrence_input_and_boundaries_fail_without_writes():
    with SessionLocal() as db:
        empty = materialize_tool_product_occurrences(db, entity_keys=set())
        with pytest.raises(ValueError, match="between 1 and 500"):
            materialize_tool_product_occurrences(db, limit=501)
        db.commit()
        assert db.scalars(select(ToolProductOccurrence)).all() == []

    assert empty["evaluated"] == 0


def test_unresolved_or_low_confidence_entities_do_not_create_occurrences():
    with SessionLocal() as db:
        item_id = _seed_item(db, source="synthetic-occurrence-low", title="Radar Tool", text="MOCK tool", index=3)
        normalize_tool_product_entities(
            db,
            normalized_item_ids={item_id},
            policy=ToolProductIdentificationPolicy(min_evidence_count=1, min_confidence=0.99),
        )
        result = materialize_tool_product_occurrences(db)
        db.commit()

    assert result["evaluated"] == 0


def test_occurrence_materialization_endpoint_requires_admin(monkeypatch):
    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/tool-products/occurrences/materialize")
    assert response.status_code == 401
