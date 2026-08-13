from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.domain.keyword_burst import (
    BurstComparison,
    KeywordBurstInput,
    KeywordBurstPolicy,
    burst_windows,
    evaluate_keyword_burst,
)


def test_burst_contract_uses_half_open_windows_and_detects_anomaly():
    policy = KeywordBurstPolicy(current_window_days=3, baseline_window_days=6, min_current_observations=6, min_absolute_delta=4, min_growth_rate=0.5, min_z_score=2.0)
    start, end, baseline_start, baseline_end = burst_windows(date(2026, 8, 12), policy)
    assert (start, end, baseline_start, baseline_end) == (date(2026, 8, 9), date(2026, 8, 12), date(2026, 8, 3), date(2026, 8, 9))
    points = {day: 1 for day in (date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 8))}
    points.update({date(2026, 8, 9): 4, date(2026, 8, 10): 5, date(2026, 8, 11): 6})
    evaluation = evaluate_keyword_burst(KeywordBurstInput(keyword_id=1, keyword="burst", window_end=date(2026, 8, 12), daily_observations=points, daily_sources={day: 2 for day in points}), policy=policy, evaluated_at=datetime(2026, 8, 12, 12))
    assert evaluation.anomalous is True
    assert evaluation.comparison == BurstComparison.BURST
    assert evaluation.current_observations == 15
    assert evaluation.baseline_observations == 6
    assert evaluation.absolute_delta == 9
    assert evaluation.input_signature


def test_burst_contract_zero_fills_missing_days_and_fails_closed_on_empty_input():
    policy = KeywordBurstPolicy(current_window_days=3, baseline_window_days=3, min_current_observations=2, min_current_sources=1)
    evaluation = evaluate_keyword_burst(KeywordBurstInput(keyword_id=2, keyword="new", window_end=date(2026, 8, 12), daily_observations={date(2026, 8, 10): 3}, daily_sources={date(2026, 8, 10): 1}), policy=policy)
    assert evaluation.comparison == BurstComparison.NEW_SIGNAL
    assert evaluation.baseline_observations == 0
    assert evaluation.current_observations == 3
    assert evaluation.anomalous is True

    empty = evaluate_keyword_burst(KeywordBurstInput(keyword_id=3, keyword="empty", window_end=date(2026, 8, 12)), policy=policy)
    assert empty.anomalous is False
    assert empty.current_observations == 0


def test_burst_contract_rejects_unbounded_or_invalid_policy_and_counts():
    with pytest.raises(ValidationError):
        KeywordBurstPolicy(current_window_days=30, baseline_window_days=90)
    with pytest.raises(ValidationError):
        KeywordBurstInput(keyword_id=1, keyword="bad", window_end=date(2026, 8, 12), daily_observations={date(2026, 8, 11): -1})
