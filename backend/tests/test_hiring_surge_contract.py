from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.domain.hiring_surge import (
    HiringComparison,
    HiringSurgeInput,
    HiringSurgePolicy,
    evaluate_hiring_surge,
    hiring_windows,
)


def test_hiring_contract_detects_growth_with_complete_window_math():
    policy = HiringSurgePolicy(current_window_days=3, baseline_window_days=6, min_current_jobs=6, min_absolute_delta=4, min_growth_rate=0.5, min_z_score=2.0, min_current_evidence=2)
    start, end, baseline_start, baseline_end = hiring_windows(date(2026, 8, 12), policy)
    assert (start, end, baseline_start, baseline_end) == (date(2026, 8, 9), date(2026, 8, 12), date(2026, 8, 3), date(2026, 8, 9))
    jobs = {day: 1 for day in (date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 8))}
    jobs.update({date(2026, 8, 9): 4, date(2026, 8, 10): 5, date(2026, 8, 11): 6})
    evaluation = evaluate_hiring_surge(
        HiringSurgeInput(keyword_id=1, keyword="synthetic hiring", window_end=date(2026, 8, 12), daily_jobs=jobs, daily_sources={day: 2 for day in jobs}, daily_evidence={day: 2 for day in jobs}),
        policy=policy,
        evaluated_at=datetime(2026, 8, 12, 12),
    )
    assert evaluation.surge is True
    assert evaluation.comparison == HiringComparison.SURGE
    assert evaluation.current_jobs == 15
    assert evaluation.baseline_jobs == 6
    assert evaluation.absolute_delta == 9
    assert evaluation.input_signature


def test_hiring_contract_zero_fills_new_signal_and_fails_closed_on_empty():
    policy = HiringSurgePolicy(current_window_days=3, baseline_window_days=3, min_current_jobs=2, min_current_sources=1, min_current_evidence=1)
    new_signal = evaluate_hiring_surge(HiringSurgeInput(keyword_id=2, keyword="new jobs", window_end=date(2026, 8, 12), daily_jobs={date(2026, 8, 10): 3}, daily_sources={date(2026, 8, 10): 1}, daily_evidence={date(2026, 8, 10): 1}), policy=policy)
    assert new_signal.comparison == HiringComparison.NEW_SIGNAL
    assert new_signal.baseline_jobs == 0
    assert new_signal.current_jobs == 3
    assert new_signal.surge is True

    empty = evaluate_hiring_surge(HiringSurgeInput(keyword_id=3, keyword="empty jobs", window_end=date(2026, 8, 12)), policy=policy)
    assert empty.surge is False
    assert empty.current_jobs == 0


def test_hiring_contract_rejects_unbounded_or_negative_inputs():
    with pytest.raises(ValidationError):
        HiringSurgePolicy(current_window_days=30, baseline_window_days=90)
    with pytest.raises(ValidationError):
        HiringSurgeInput(keyword_id=1, keyword="bad", window_end=date(2026, 8, 12), daily_jobs={date(2026, 8, 11): -1})
