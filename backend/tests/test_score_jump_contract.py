from datetime import datetime, timedelta, timezone

from app.domain.score_jump import (
    SCORE_JUMP_ALGORITHM_VERSION,
    ScoreJumpInput,
    ScoreJumpPolicy,
    ScoreJumpStatus,
    ScoreSnapshotInput,
    evaluate_score_jump,
)


def _snapshot(*, score: float, when: datetime, model_version: str = "score-v1", opportunity_id: int = 7, marker: str = "a") -> ScoreSnapshotInput:
    return ScoreSnapshotInput(
        opportunity_id=opportunity_id,
        model_version=model_version,
        input_signature=marker * 64,
        score=score,
        risk_score=20.0,
        stage="VALIDATED",
        evidence_count=3,
        breakdown={"data_class": "SYNTHETIC", "total": score},
        calculated_at=when,
    )


def test_score_jump_requires_absolute_and_relative_thresholds():
    result = evaluate_score_jump(
        ScoreJumpInput(
            opportunity_id=7,
            previous=_snapshot(score=40.0, when=datetime(2026, 8, 1), marker="a"),
            current=_snapshot(score=60.0, when=datetime(2026, 8, 2), marker="b"),
        ),
        evaluated_at=datetime(2026, 8, 12),
    )
    assert result.status == ScoreJumpStatus.SCORE_JUMP
    assert result.jumped is True
    assert result.absolute_delta == 20.0
    assert result.relative_delta == 0.5
    assert result.algorithm_version == SCORE_JUMP_ALGORITHM_VERSION


def test_score_jump_is_not_triggered_when_either_threshold_fails():
    absolute_fail = evaluate_score_jump(
        ScoreJumpInput(opportunity_id=7, previous=_snapshot(score=40.0, when=datetime(2026, 8, 1)), current=_snapshot(score=54.0, when=datetime(2026, 8, 2))),
    )
    relative_fail = evaluate_score_jump(
        ScoreJumpInput(opportunity_id=7, previous=_snapshot(score=90.0, when=datetime(2026, 8, 1)), current=_snapshot(score=100.0, when=datetime(2026, 8, 2))),
    )
    assert absolute_fail.status == ScoreJumpStatus.NO_JUMP
    assert relative_fail.status == ScoreJumpStatus.NO_JUMP
    assert not absolute_fail.jumped and not relative_fail.jumped


def test_score_jump_version_and_sequence_constraints_fail_closed():
    version_mismatch = evaluate_score_jump(
        ScoreJumpInput(opportunity_id=7, previous=_snapshot(score=20, when=datetime(2026, 8, 1), model_version="score-v1"), current=_snapshot(score=50, when=datetime(2026, 8, 2), model_version="score-v2")),
    )
    no_baseline = evaluate_score_jump(ScoreJumpInput(opportunity_id=7, current=_snapshot(score=50, when=datetime(2026, 8, 2))))
    invalid_time = evaluate_score_jump(
        ScoreJumpInput(opportunity_id=7, previous=_snapshot(score=20, when=datetime(2026, 8, 2)), current=_snapshot(score=50, when=datetime(2026, 8, 2))),
    )
    assert version_mismatch.status == ScoreJumpStatus.VERSION_MISMATCH
    assert no_baseline.status == ScoreJumpStatus.NO_BASELINE
    assert invalid_time.status == ScoreJumpStatus.INVALID_SEQUENCE


def test_score_jump_normalizes_timezone_checks_gap_and_signature_is_stable():
    previous = _snapshot(score=20, when=datetime(2026, 8, 1, tzinfo=timezone.utc), marker="a")
    current = _snapshot(score=50, when=datetime(2026, 8, 2, tzinfo=timezone.utc), marker="b")
    first = evaluate_score_jump(ScoreJumpInput(opportunity_id=7, previous=previous, current=current), evaluated_at=datetime(2026, 8, 12))
    second = evaluate_score_jump(ScoreJumpInput(opportunity_id=7, previous=previous, current=current), evaluated_at=datetime(2026, 8, 13))
    assert previous.calculated_at.tzinfo is None
    assert first.input_signature == second.input_signature
    too_old = evaluate_score_jump(
        ScoreJumpInput(opportunity_id=7, previous=_snapshot(score=10, when=datetime(2025, 1, 1)), current=_snapshot(score=50, when=datetime(2026, 8, 2))),
        policy=ScoreJumpPolicy(max_lookback_days=90),
    )
    assert too_old.status == ScoreJumpStatus.INVALID_SEQUENCE
