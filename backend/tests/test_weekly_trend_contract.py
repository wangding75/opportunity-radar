from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.weekly_trends import (
    WEEKLY_TREND_ALGORITHM_VERSION,
    WEEKLY_TREND_CONTRACT_VERSION,
    TrendComparison,
    TrendEvidenceProvenance,
    WeeklyTrendItem,
    WeeklyTrendPolicy,
    WeeklyTrendReport,
    WeeklyTrendStatus,
    build_weekly_trend_input_signature,
    completed_week_window,
)


def _item(*, keyword_id=1, baseline=4, current=8, comparison=TrendComparison.GROWING):
    return WeeklyTrendItem(
        rank=1,
        keyword_id=keyword_id,
        keyword="synthetic trend",
        comparison=comparison,
        current_observations=current,
        baseline_observations=baseline,
        current_sources=2,
        baseline_sources=1,
        absolute_delta=current - baseline,
        growth_rate=(current - baseline) / baseline if baseline else None,
        momentum_score=72,
        trend_signature="a" * 64,
        last_seen_at=datetime(2026, 8, 9, 23, tzinfo=timezone.utc),
        evidence_provenance=TrendEvidenceProvenance.SYNTHETIC,
        selection_reasons=["synthetic growth signal"],
    )


def _report(*, status=WeeklyTrendStatus.READY, items=None, total_candidates=1, **overrides):
    defaults = {
        "week_start": date(2026, 8, 3),
        "week_end": date(2026, 8, 10),
        "baseline_start": date(2026, 7, 27),
        "baseline_end": date(2026, 8, 3),
        "generated_at": datetime(2026, 8, 12, 12),
        "status": status,
        "policy": WeeklyTrendPolicy(),
        "total_candidates": total_candidates,
        "selected_count": len(items or []),
        "input_signature": "b" * 64,
        "items": items or [],
    }
    defaults.update(overrides)
    return WeeklyTrendReport(**defaults)


def test_completed_week_window_is_previous_full_utc_week():
    assert completed_week_window(date(2026, 8, 12)) == (
        date(2026, 8, 3), date(2026, 8, 10), date(2026, 7, 27), date(2026, 8, 3)
    )
    assert completed_week_window(date(2026, 8, 10))[1] == date(2026, 8, 10)


def test_weekly_report_contract_preserves_versions_and_empty_semantics():
    report = _report(items=[_item()])
    assert report.contract_version == WEEKLY_TREND_CONTRACT_VERSION
    assert report.algorithm_version == WEEKLY_TREND_ALGORITHM_VERSION
    assert report.status == WeeklyTrendStatus.READY
    empty = _report(status=WeeklyTrendStatus.EMPTY, items=[], total_candidates=0)
    assert empty.items == []


def test_baseline_zero_is_explicit_new_signal_not_infinite_growth():
    item = _item(baseline=0, current=3, comparison=TrendComparison.NEW_SIGNAL)
    assert item.growth_rate is None
    assert item.comparison == TrendComparison.NEW_SIGNAL
    with pytest.raises(ValidationError, match="baseline-zero"):
        _item(baseline=0, current=3, comparison=TrendComparison.GROWING)


def test_declining_comparison_preserves_negative_growth_rate():
    item = _item(baseline=10, current=5, comparison=TrendComparison.DECLINING)
    assert item.growth_rate == -0.5


def test_weekly_report_rejects_wrong_window_duplicate_keyword_or_empty_success():
    with pytest.raises(ValidationError, match="Monday-to-Monday"):
        _report(week_start=date(2026, 8, 4), week_end=date(2026, 8, 11), items=[_item()])
    with pytest.raises(ValidationError, match="duplicate keyword_id"):
        _report(items=[_item(keyword_id=1), _item(keyword_id=1).model_copy(update={"rank": 2})], total_candidates=2)
    with pytest.raises(ValidationError, match="READY trend report"):
        _report(status=WeeklyTrendStatus.READY, items=[], total_candidates=0)


def test_weekly_input_signature_is_order_independent_but_meaning_sensitive():
    policy = WeeklyTrendPolicy()
    first = {"keyword_id": 2, "keyword": "b", "current_observations": 8, "baseline_observations": 4, "absolute_delta": 4, "momentum_score": 70, "trend_signature": "b" * 64}
    second = {"keyword_id": 1, "keyword": "a", "current_observations": 10, "baseline_observations": 3, "absolute_delta": 7, "momentum_score": 80, "trend_signature": "a" * 64}
    signature_a = build_weekly_trend_input_signature(week_start=date(2026, 8, 3), week_end=date(2026, 8, 10), baseline_start=date(2026, 7, 27), baseline_end=date(2026, 8, 3), candidates=[first, second], policy=policy)
    signature_b = build_weekly_trend_input_signature(week_start=date(2026, 8, 3), week_end=date(2026, 8, 10), baseline_start=date(2026, 7, 27), baseline_end=date(2026, 8, 3), candidates=[second, first], policy=policy)
    assert signature_a == signature_b
    assert build_weekly_trend_input_signature(week_start=date(2026, 8, 3), week_end=date(2026, 8, 10), baseline_start=date(2026, 7, 27), baseline_end=date(2026, 8, 3), candidates=[dict(first, current_observations=9), second], policy=policy) != signature_a
