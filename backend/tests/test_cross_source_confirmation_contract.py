from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.domain.citations import CitationProvenance
from app.domain.cross_source_confirmation import (
    ConfirmationStatus,
    CrossSourceConfirmationInput,
    CrossSourceConfirmationPolicy,
    CrossSourceEvidence,
    evaluate_cross_source_confirmation,
    source_endpoint_key,
)


NOW = datetime(2026, 8, 12, 12)


def _evidence(index: str, *, source: str, title: str, text: str, url: str, observed_at: datetime = NOW) -> CrossSourceEvidence:
    return CrossSourceEvidence(
        evidence_id="ev1_" + index * 64,
        source_id=source,
        title=title,
        text=text,
        url=url,
        observed_at=observed_at,
        provenance=CitationProvenance.SYNTHETIC,
    )


def test_confirmation_requires_two_independent_endpoints_and_two_claims():
    result = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="opp:cross-source",
            evidence=[
                _evidence("a", source="source-a", title="Hiring plan A", text="Acme is hiring platform engineers", url="https://a.example/jobs/1"),
                _evidence("b", source="source-b", title="Hiring plan B", text="Acme opened a platform engineering team", url="https://b.example/jobs/9"),
            ],
        ),
        evaluated_at=NOW,
    )

    assert result.status == ConfirmationStatus.CONFIRMED
    assert result.confirmed is True
    assert result.independent_source_count == 2
    assert result.unique_claim_count == 2
    assert result.source_endpoints == ["host:a.example", "host:b.example"]
    assert result.algorithm_version == "cross-source-confirmation-v1"


def test_empty_and_syndicated_or_same_endpoint_evidence_fail_closed():
    empty = evaluate_cross_source_confirmation(CrossSourceConfirmationInput(subject_key="empty"), evaluated_at=NOW)
    assert empty.status == ConfirmationStatus.NO_EVIDENCE
    assert empty.confirmed is False

    syndicated = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="syndicated",
            evidence=[
                _evidence("a", source="source-a", title="Same", text="same syndicated text", url="https://a.example/one"),
                _evidence("b", source="source-b", title="Same", text="same syndicated text", url="https://b.example/two"),
            ],
        ),
        evaluated_at=NOW,
    )
    assert syndicated.status == ConfirmationStatus.INSUFFICIENT_EVIDENCE
    assert syndicated.independent_source_count == 2
    assert syndicated.unique_claim_count == 1
    assert syndicated.deduplicated_evidence_count == 1

    same_endpoint = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="same-endpoint",
            evidence=[
                _evidence("c", source="different-id-a", title="One", text="claim one", url="https://www.example.com/jobs/1"),
                _evidence("d", source="different-id-b", title="Two", text="claim two", url="https://example.com/jobs/2"),
            ],
        ),
        evaluated_at=NOW,
    )
    assert same_endpoint.independent_source_count == 1
    assert same_endpoint.confirmed is False


def test_duplicate_execution_signature_is_order_independent_and_invalid_ids_are_rejected():
    first_input = CrossSourceConfirmationInput(
        subject_key="order-independent",
        evidence=[
            _evidence("a", source="source-a", title="One", text="claim one", url="https://a.example/1"),
            _evidence("b", source="source-b", title="Two", text="claim two", url="https://b.example/2"),
        ],
    )
    second_input = CrossSourceConfirmationInput(subject_key="order-independent", evidence=list(reversed(first_input.evidence)))
    first = evaluate_cross_source_confirmation(first_input, evaluated_at=NOW)
    second = evaluate_cross_source_confirmation(second_input, evaluated_at=NOW)
    assert first.input_signature == second.input_signature
    assert first.evidence_ids == second.evidence_ids

    with pytest.raises(ValidationError):
        CrossSourceEvidence(evidence_id="not-an-evidence-id", source_id="source", observed_at=NOW)


def test_time_boundaries_keep_exact_cutoff_and_exclude_future_or_stale_evidence():
    policy = CrossSourceConfirmationPolicy(max_age_hours=24)
    result = evaluate_cross_source_confirmation(
        CrossSourceConfirmationInput(
            subject_key="time-boundary",
            evidence=[
                _evidence("a", source="source-a", title="Cutoff", text="at cutoff", url="https://a.example/1", observed_at=NOW - timedelta(hours=24)),
                _evidence("b", source="source-b", title="Now", text="at now", url="https://b.example/2", observed_at=NOW.replace(tzinfo=timezone.utc)),
                _evidence("c", source="source-c", title="Future", text="future", url="https://c.example/3", observed_at=NOW + timedelta(seconds=1)),
                _evidence("d", source="source-d", title="Stale", text="stale", url="https://d.example/4", observed_at=NOW - timedelta(hours=24, seconds=1)),
            ],
        ),
        policy=policy,
        evaluated_at=NOW.replace(tzinfo=timezone.utc),
    )

    assert result.confirmed is True
    assert result.fresh_evidence_count == 2
    assert result.stale_evidence_count == 1
    assert result.future_evidence_count == 1
    assert "excluded future evidence count=1" in result.reasons


def test_source_endpoint_falls_back_to_normalized_source_id_without_url():
    assert source_endpoint_key(" Source A ") == "source:source-a"
    assert source_endpoint_key("Source A", "https://www.Example.com/path") == "host:example.com"
