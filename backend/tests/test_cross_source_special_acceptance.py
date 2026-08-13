from datetime import datetime

import pytest

from app.domain.citations import CitationProvenance
from app.domain.cross_source_confirmation import (
    ConfirmationStatus,
    CrossSourceConfirmationInput,
    CrossSourceConfirmationPolicy,
    CrossSourceEvidence,
    evaluate_cross_source_confirmation,
)


NOW = datetime(2026, 8, 12, 12)


def _evidence(index: int, *, source: str, title: str, text: str, url: str) -> CrossSourceEvidence:
    return CrossSourceEvidence(
        evidence_id="ev1_" + f"{index:064x}",
        source_id=source,
        title=title,
        text=text,
        url=url,
        observed_at=NOW,
        provenance=CitationProvenance.SYNTHETIC,
    )


def test_conflicting_same_topic_from_independent_sources_is_fail_closed():
    result = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="synthetic-conflict",
            evidence=[
                _evidence(1, source="synthetic-a", title="Pricing", text="SYNTHETIC price is 10", url="https://a.synthetic.invalid/1"),
                _evidence(2, source="synthetic-b", title="Pricing", text="SYNTHETIC price is 100", url="https://b.synthetic.invalid/2"),
            ],
        ),
        evaluated_at=NOW,
    )
    assert result.status == ConfirmationStatus.INSUFFICIENT_EVIDENCE
    assert result.confirmed is False
    assert result.conflict_count == 1
    assert "conflicting claim groups=pricing" in result.reasons


def test_evidence_overload_is_rejected_by_policy_before_scoring():
    evidence = [
        _evidence(index, source=f"synthetic-{index}", title=f"Claim {index}", text=f"SYNTHETIC claim {index}", url=f"https://{index}.synthetic.invalid/{index}")
        for index in range(1, 22)
    ]
    with pytest.raises(ValueError, match="max_evidence"):
        evaluate_cross_source_confirmation(
            CrossSourceConfirmationInput(subject_key="synthetic-overload", evidence=evidence),
            policy=CrossSourceConfirmationPolicy(max_evidence=20),
            evaluated_at=NOW,
        )


def test_repeated_source_endpoint_never_becomes_independent_confirmation():
    result = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="synthetic-repeated-source",
            evidence=[
                _evidence(30, source="synthetic-a", title="Claim A", text="SYNTHETIC A", url="https://same.synthetic.invalid/1"),
                _evidence(31, source="synthetic-b", title="Claim B", text="SYNTHETIC B", url="https://same.synthetic.invalid/2"),
                _evidence(32, source="synthetic-c", title="Claim C", text="SYNTHETIC C", url="https://same.synthetic.invalid/3"),
            ],
        ),
        evaluated_at=NOW,
    )
    assert result.independent_source_count == 1
    assert result.status == ConfirmationStatus.INSUFFICIENT_EVIDENCE
    assert result.confirmed is False
