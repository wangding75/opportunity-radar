from datetime import datetime, timedelta, timezone

from app.domain.high_signal import HighSignalInput, HighSignalTriggerPolicy, high_signal_dedupe_key
from app.services.high_signal import evaluate_high_signal


def _input(**overrides) -> HighSignalInput:
    values = {
        "opportunity_id": 7,
        "opportunity_key": "opp:high-signal",
        "title": "High signal opportunity",
        "stage": "EARLY_GROWTH",
        "score": 88,
        "risk_score": 20,
        "evidence_count": 5,
        "cross_source_score": 10,
        "analysis_status": "READY",
        "analysis_signature": "a" * 64,
        "score_version": "score-v1",
        "updated_at": datetime(2026, 8, 12, 10),
    }
    values.update(overrides)
    return HighSignalInput(**values)


def test_high_signal_evaluation_is_eligible_and_explains_all_conditions():
    result = evaluate_high_signal(_input(), now=datetime(2026, 8, 12, 12))
    assert result.eligible is True
    assert len(result.trigger_reasons) == 7
    assert result.failed_conditions == []
    assert len(result.dedupe_key) == 64


def test_high_signal_evaluation_reports_each_failed_condition_and_is_fail_closed():
    result = evaluate_high_signal(
        _input(score=70, risk_score=60, evidence_count=1, cross_source_score=0, stage="DORMANT", analysis_status="FAILED", updated_at=datetime(2026, 8, 1)),
        now=datetime(2026, 8, 12),
    )
    assert result.eligible is False
    assert len(result.failed_conditions) == 7
    assert any("score" in reason for reason in result.failed_conditions)
    assert any("excluded" in reason for reason in result.failed_conditions)
    assert result.trigger_reasons == []


def test_high_signal_dedupe_key_ignores_time_but_changes_with_signal_state_or_policy():
    policy = HighSignalTriggerPolicy()
    first = _input(updated_at=datetime(2026, 8, 12, 1))
    second = _input(updated_at=datetime(2026, 8, 12, 23))
    assert high_signal_dedupe_key(first, policy) == high_signal_dedupe_key(second, policy)
    assert high_signal_dedupe_key(first, policy) != high_signal_dedupe_key(_input(score=89), policy)
    assert high_signal_dedupe_key(first, policy) != high_signal_dedupe_key(first, HighSignalTriggerPolicy(min_score=85))


def test_high_signal_normalizes_timezone_and_rejects_future_signal():
    signal = _input(updated_at=datetime(2026, 8, 12, 12, tzinfo=timezone.utc))
    result = evaluate_high_signal(signal, now=datetime(2026, 8, 12, 11))
    assert signal.updated_at.tzinfo is None
    assert result.eligible is False
    assert "future" in result.failed_conditions[0]
