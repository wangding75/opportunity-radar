from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.domain.digest import (
    DIGEST_ALGORITHM_VERSION,
    DIGEST_CONTRACT_VERSION,
    DigestEvidenceProvenance,
    DigestSelectionPolicy,
    DigestStatus,
    DailyDigest,
    DigestItem,
    build_digest_input_signature,
)


def _item(rank: int = 1, *, opportunity_id: int = 7) -> DigestItem:
    return DigestItem(
        rank=rank,
        opportunity_id=opportunity_id,
        opportunity_key=f"opp:contract:{opportunity_id}",
        title="Contract opportunity",
        stage="DISCOVERY",
        score=82.5,
        risk_score=18.0,
        evidence_count=3,
        summary="Explainable summary",
        analysis_status="READY",
        analysis_provider="heuristic",
        analysis_signature="a" * 64,
        last_seen_at=datetime(2026, 8, 12, 6, 0, 0, tzinfo=timezone.utc),
        evidence_ids=["ev1_" + "b" * 64],
        evidence_provenance=DigestEvidenceProvenance.OBSERVED,
        selection_reasons=["score above configured daily threshold"],
        score_breakdown={"model_version": "score-v1", "total": 82.5},
    )


def _digest(*, status=DigestStatus.READY, items=None, total_candidates=1, **overrides):
    day = date(2026, 8, 12)
    defaults = {
        "digest_date": day,
        "window_start": datetime(2026, 8, 12),
        "window_end": datetime(2026, 8, 13),
        "generated_at": datetime(2026, 8, 12, 12),
        "status": status,
        "selection_policy": DigestSelectionPolicy(),
        "total_candidates": total_candidates,
        "selected_count": len(items or []),
        "input_signature": "c" * 64,
        "items": items or [],
    }
    defaults.update(overrides)
    return DailyDigest(**defaults)


def test_contract_normalizes_external_time_to_utc_naive_and_preserves_versions():
    digest = _digest(items=[_item()])
    assert digest.contract_version == DIGEST_CONTRACT_VERSION
    assert digest.algorithm_version == DIGEST_ALGORITHM_VERSION
    assert digest.window_start.tzinfo is None
    assert digest.items[0].last_seen_at.tzinfo is None
    assert digest.status == DigestStatus.READY


def test_empty_daily_digest_is_valid_and_unambiguous():
    digest = _digest(status=DigestStatus.EMPTY, items=[], total_candidates=0)
    assert digest.selected_count == 0
    assert digest.model_dump(mode="json")["items"] == []


def test_digest_rejects_duplicate_items_or_non_contiguous_ranks():
    with pytest.raises(ValidationError, match="duplicate opportunity_id"):
        _digest(items=[_item(1), _item(2)], total_candidates=2)
    with pytest.raises(ValidationError, match="contiguous"):
        _digest(items=[_item(2)], total_candidates=1)


def test_digest_rejects_empty_success_and_unexplained_degradation():
    with pytest.raises(ValidationError, match="READY digest must contain"):
        _digest(items=[], total_candidates=0)
    with pytest.raises(ValidationError, match="explain the degradation"):
        _digest(status=DigestStatus.DEGRADED, items=[], total_candidates=0)
    degraded = _digest(status=DigestStatus.DEGRADED, items=[], total_candidates=0, warnings=["provider data was stale"])
    assert degraded.status == DigestStatus.DEGRADED


def test_input_signature_is_stable_across_candidate_order_and_changes_with_meaning():
    policy = DigestSelectionPolicy()
    first = {"opportunity_id": 2, "opportunity_key": "b", "score": 70, "risk_score": 20, "evidence_count": 2, "last_seen_at": "2026-08-12T01:00:00", "analysis_signature": "b" * 64}
    second = {"opportunity_id": 1, "opportunity_key": "a", "score": 80, "risk_score": 10, "evidence_count": 3, "last_seen_at": "2026-08-12T02:00:00", "analysis_signature": "a" * 64}
    signature_a = build_digest_input_signature(
        digest_date=date(2026, 8, 12),
        window_start=datetime(2026, 8, 12),
        window_end=datetime(2026, 8, 13),
        candidates=[first, second],
        selection_policy=policy,
    )
    signature_b = build_digest_input_signature(
        digest_date=date(2026, 8, 12),
        window_start=datetime(2026, 8, 12, tzinfo=timezone.utc),
        window_end=datetime(2026, 8, 13, tzinfo=timezone.utc),
        candidates=[second, first],
        selection_policy=policy,
    )
    assert signature_a == signature_b
    changed = dict(first, score=71)
    assert build_digest_input_signature(
        digest_date=date(2026, 8, 12),
        window_start=datetime(2026, 8, 12),
        window_end=datetime(2026, 8, 13),
        candidates=[changed, second],
        selection_policy=policy,
    ) != signature_a
