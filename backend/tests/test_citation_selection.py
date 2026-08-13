from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.services.citations import bind_citation_selection, select_evidence_citations


def _row(evidence_id: str, source: str, evidence_type: str, quality: str, age: int) -> dict:
    return {
        "evidence_id": f"ev1_{evidence_id * 64}"[:68],
        "source": source,
        "type": evidence_type,
        "item_type": "CONTENT",
        "quality": quality,
        "title": f"{source}-{evidence_type}",
        "text": "evidence",
        "observed_at": datetime(2026, 8, 12) - timedelta(days=age),
    }


def test_selector_prioritizes_quality_then_preserves_source_type_diversity():
    rows = [
        _row("a", "source-a", "DEMAND", "C", 0),
        _row("b", "source-a", "DEMAND", "A", 1),
        _row("c", "source-b", "SUPPLY", "B", 10),
        _row("d", "source-c", "DEMAND", "D", 0),
    ]
    selected = select_evidence_citations(rows, limit=3)
    assert [row["evidence_id"] for row in selected] == [rows[1]["evidence_id"], rows[2]["evidence_id"], rows[3]["evidence_id"]]
    assert [row["citation_rank"] for row in selected] == [1, 2, 3]
    assert selected[0]["citation_reason"] == "diverse_source_type"


def test_selector_deduplicates_ids_and_is_idempotent_for_empty_input():
    row = _row("a", "source-a", "DEMAND", "C", 0)
    duplicate = {**row, "quality": "A", "title": "better duplicate"}
    selected = select_evidence_citations([row, duplicate], limit=10)
    assert len(selected) == 1
    assert selected[0]["quality"] == "A"
    assert select_evidence_citations([], limit=10) == []
    assert select_evidence_citations([row], limit=0) == []


def test_selector_rejects_unbound_rows_and_binding_is_explicit():
    with pytest.raises(ValueError, match="requires observed_at"):
        select_evidence_citations([{"source": "source", "type": "DEMAND"}], limit=1)
    bound = bind_citation_selection([_row("a", "source-a", "DEMAND", "C", 0)], binding_type="opportunity", binding_id=42, limit=1)
    assert bound["binding"] == {"entity_type": "opportunity", "entity_id": "42"}
    assert bound["citations"][0]["evidence_id"].startswith("ev1_")
