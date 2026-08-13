from datetime import datetime

import pytest
from pydantic import ValidationError

from app.domain.citations import evidence_id_for_row
from app.domain.tool_product import (
    ToolProductIdentificationInput,
    ToolProductIdentificationPolicy,
    ToolProductKind,
    ToolProductStatus,
    ToolProductEvidence,
    identify_tool_product,
    normalize_tool_product_name,
    tool_product_entity_key,
)


def _evidence(title: str, source: str, *, observed_at: str) -> ToolProductEvidence:
    row = {"source": source, "type": "PRODUCT", "item_type": "PRODUCT", "title": title, "text": "SYNTHETIC software tool product", "observed_at": observed_at, "provenance": "SYNTHETIC"}
    return ToolProductEvidence(evidence_id=evidence_id_for_row(row), source=source, title=title, text=row["text"], item_type="PRODUCT", observed_at=observed_at, provenance="SYNTHETIC")


def test_tool_product_contract_identifies_deduplicated_tool_with_stable_key():
    first = _evidence("Acme Copilot Tool", "synthetic-a", observed_at="2026-08-12T01:00:00Z")
    second = _evidence("Acme Copilot Tool", "synthetic-b", observed_at="2026-08-12T02:00:00Z")
    result = identify_tool_product(ToolProductIdentificationInput(candidate_name=" ACME  Copilot Tool ", evidence=[first, first, second]), evaluated_at=datetime(2026, 8, 12, 3))
    assert result.status == ToolProductStatus.IDENTIFIED
    assert result.kind == ToolProductKind.TOOL
    assert result.entity_key == tool_product_entity_key("acme copilot tool", ToolProductKind.TOOL)
    assert result.deduplicated_count == 1
    assert result.evidence_count == 2
    assert result.source_count == 2
    assert result.first_seen_at < result.last_seen_at
    repeat = identify_tool_product(ToolProductIdentificationInput(candidate_name="acme copilot tool", evidence=[second, first]), evaluated_at=datetime(2026, 8, 12, 9))
    assert repeat.input_signature == result.input_signature
    assert repeat.entity_key == result.entity_key


def test_tool_product_contract_fails_closed_for_empty_ambiguous_and_low_confidence_inputs():
    empty = identify_tool_product(ToolProductIdentificationInput())
    assert empty.status == ToolProductStatus.INSUFFICIENT_EVIDENCE
    assert empty.entity_key is None

    ambiguous_evidence = [ToolProductEvidence(evidence_id=evidence_id_for_row({"source": source, "type": "CONTENT", "item_type": "CONTENT", "title": "Acme", "text": "SYNTHETIC market mention", "observed_at": timestamp}), source=source, title="Acme", text="SYNTHETIC market mention", item_type="CONTENT", observed_at=timestamp, provenance="SYNTHETIC") for source, timestamp in (("synthetic-a", "2026-08-12T01:00:00Z"), ("synthetic-b", "2026-08-12T02:00:00Z"))]
    ambiguous = identify_tool_product(ToolProductIdentificationInput(candidate_name="Acme", evidence=ambiguous_evidence))
    assert ambiguous.status == ToolProductStatus.UNRESOLVED
    assert ambiguous.entity_key is None

    policy = ToolProductIdentificationPolicy(min_confidence=0.95)
    low = identify_tool_product(ToolProductIdentificationInput(candidate_name="Acme Tool", evidence=[_evidence("Acme Tool", "synthetic-a", observed_at="2026-08-12T01:00:00Z"), _evidence("Acme Tool listing", "synthetic-a", observed_at="2026-08-12T02:00:00Z")]), policy=policy)
    assert low.status == ToolProductStatus.LOW_CONFIDENCE
    assert low.entity_key is not None


def test_tool_product_contract_rejects_invalid_ids_and_key_boundaries():
    with pytest.raises(ValidationError):
        ToolProductEvidence(evidence_id="bad", source="synthetic", observed_at="2026-08-12T00:00:00Z")
    with pytest.raises(ValueError):
        tool_product_entity_key("", ToolProductKind.TOOL)
    assert normalize_tool_product_name("Ａcme — Copilot!") == "acme copilot"
