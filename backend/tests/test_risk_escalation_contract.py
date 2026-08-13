from datetime import datetime, timedelta, timezone

import pytest

from app.domain.risk_escalation import (
    RiskEscalationInput,
    RiskEscalationLevel,
    RiskEscalationPolicy,
    RiskEscalationStatus,
    RiskSnapshotInput,
    classify_risk_level,
    evaluate_risk_escalation,
)


def _snapshot(*, risk_score: float = 20.0, calculated_at: datetime = datetime(2026, 8, 1), model_version: str = "risk-v1", opportunity_id: int = 7) -> RiskSnapshotInput:
    return RiskSnapshotInput(
        opportunity_id=opportunity_id,
        model_version=model_version,
        input_signature=("a" if calculated_at.day == 1 else "b") * 64,
        risk_score=risk_score,
        stage="VALIDATED",
        evidence_count=2,
        breakdown={"data_class": "SYNTHETIC", "risk": risk_score},
        calculated_at=calculated_at,
    )


def test_risk_level_boundaries_are_stable_and_bounded():
    assert classify_risk_level(0) == RiskEscalationLevel.NONE
    assert classify_risk_level(19.999) == RiskEscalationLevel.NONE
    assert classify_risk_level(20) == RiskEscalationLevel.LOW
    assert classify_risk_level(40) == RiskEscalationLevel.MEDIUM
    assert classify_risk_level(60) == RiskEscalationLevel.HIGH
    assert classify_risk_level(80) == RiskEscalationLevel.CRITICAL
    assert classify_risk_level(100) == RiskEscalationLevel.CRITICAL


def test_escalation_uses_level_crossing_or_threshold_and_explains_breakdown():
    previous = _snapshot(risk_score=35)
    current = _snapshot(risk_score=50, calculated_at=datetime(2026, 8, 2))
    result = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=previous, current=current), evaluated_at=datetime(2026, 8, 12))
    assert result.status == RiskEscalationStatus.ESCALATED
    assert result.escalated is True
    assert result.previous_level == RiskEscalationLevel.LOW
    assert result.current_level == RiskEscalationLevel.MEDIUM
    assert result.absolute_delta == 15
    assert any("risk level" in reason for reason in result.reasons)


def test_stable_and_deescalated_states_are_distinct():
    stable = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=_snapshot(risk_score=20), current=_snapshot(risk_score=25, calculated_at=datetime(2026, 8, 2))))
    down = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=_snapshot(risk_score=75), current=_snapshot(risk_score=55, calculated_at=datetime(2026, 8, 2))))
    assert stable.status == RiskEscalationStatus.STABLE
    assert stable.escalated is False
    assert down.status == RiskEscalationStatus.DE_ESCALATED
    assert down.escalated is False


def test_missing_baseline_version_mismatch_and_time_bounds_fail_closed():
    current = _snapshot(risk_score=60, calculated_at=datetime(2026, 8, 2))
    no_baseline = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, current=current))
    mismatch = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=_snapshot(model_version="risk-v0"), current=current))
    too_old = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=_snapshot(calculated_at=datetime(2026, 1, 1)), current=current))
    assert no_baseline.status == RiskEscalationStatus.NO_BASELINE
    assert mismatch.status == RiskEscalationStatus.VERSION_MISMATCH
    assert too_old.status == RiskEscalationStatus.INVALID_SEQUENCE
    assert all(item.escalated is False for item in (no_baseline, mismatch, too_old))


def test_signature_is_stable_across_evaluation_time_and_invalid_policy_is_rejected():
    input = RiskEscalationInput(opportunity_id=7, previous=_snapshot(risk_score=10), current=_snapshot(risk_score=30, calculated_at=datetime(2026, 8, 2)))
    first = evaluate_risk_escalation(input, evaluated_at=datetime(2026, 8, 12, 1))
    second = evaluate_risk_escalation(input, evaluated_at=datetime(2026, 8, 12, 23))
    assert first.input_signature == second.input_signature
    with pytest.raises(ValueError, match="non-decreasing"):
        RiskEscalationPolicy(low_threshold=60, medium_threshold=40)


def test_timezone_is_normalized_and_future_current_snapshot_is_invalid():
    previous = _snapshot(risk_score=20, calculated_at=datetime(2026, 8, 1, tzinfo=timezone.utc))
    current = _snapshot(risk_score=30, calculated_at=datetime(2026, 8, 1, 12, tzinfo=timezone.utc))
    result = evaluate_risk_escalation(RiskEscalationInput(opportunity_id=7, previous=previous, current=current), evaluated_at=datetime(2026, 8, 1, 11))
    assert previous.calculated_at.tzinfo is None
    assert result.status == RiskEscalationStatus.ESCALATED
