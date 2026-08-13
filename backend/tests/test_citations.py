from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.domain.citations import (
    CITATION_CONTRACT_VERSION,
    EVIDENCE_ID_ALGORITHM,
    CitationProvenance,
    EvidenceCitation,
    evidence_id_for_content_hash,
    evidence_id_for_row,
    provenance_from_payload,
)
from app.services.opportunity_analysis import OpportunityAnalysisInput


def test_evidence_id_is_versioned_and_derived_from_content_hash_not_database_id():
    digest = "A" * 64
    assert evidence_id_for_content_hash(digest) == f"ev1_{'a' * 64}"
    assert evidence_id_for_content_hash(digest) == evidence_id_for_content_hash(digest)
    with pytest.raises(ValueError, match="64-character"):
        evidence_id_for_content_hash("not-a-hash")


def test_analysis_input_freezes_citation_version_and_adds_stable_id():
    payload = OpportunityAnalysisInput(
        title="title",
        related_keywords=["keyword"],
        stage="DISCOVERY",
        score=10,
        risk_score=0,
        evidence_types={"DEMAND": 1},
        evidence=[
            {
                "source": "source",
                "type": "DEMAND",
                "item_type": "CONTENT",
                "quality": "C",
                "acquisition_method": "MANUAL_IMPORT",
                "title": "title",
                "text": "text",
                "observed_at": datetime(2026, 8, 12, 0, 0),
            }
        ],
    )
    assert payload.citation_contract_version == CITATION_CONTRACT_VERSION
    assert payload.evidence[0]["evidence_id"].startswith("ev1_")
    assert len(payload.evidence[0]["evidence_id"]) == 68


def test_evidence_citation_validates_frozen_provider_shape():
    citation = EvidenceCitation(
        evidence_id=evidence_id_for_content_hash("b" * 64),
        source="source",
        type="DEMAND",
        item_type="CONTENT",
        quality="C",
        acquisition_method="MANUAL_IMPORT",
        title="title",
        text="text",
        observed_at=datetime(2026, 8, 12, 0, 0),
        provenance=CitationProvenance.SYNTHETIC,
    )
    assert citation.provenance == CitationProvenance.SYNTHETIC
    with pytest.raises(ValidationError):
        EvidenceCitation(
            evidence_id="database-row-1",
            source="source",
            type="DEMAND",
            item_type="CONTENT",
            quality="C",
            acquisition_method="MANUAL_IMPORT",
            observed_at=datetime(2026, 8, 12, 0, 0),
        )


def test_standalone_rows_have_deterministic_fallback_and_explicit_mock_marker():
    row = {"source": "mock", "type": "DEMAND", "title": "x", "text": "y", "observed_at": "2026-08-12T00:00:00"}
    assert evidence_id_for_row(row) == evidence_id_for_row(dict(row))
    assert provenance_from_payload({"_provenance": "synthetic"}) == CitationProvenance.SYNTHETIC
    assert provenance_from_payload({"data_class": "MOCK"}) == CitationProvenance.MOCK
    assert EVIDENCE_ID_ALGORITHM == "sha256-content-hash-v1"
