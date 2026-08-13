from app.domain.cross_source_score import CrossSourceScoreInput, CrossSourceScorePolicy, score_cross_source_confirmation


def _input(**overrides):
    values = {
        "confirmation_status": "CONFIRMED",
        "confirmed": True,
        "independent_source_count": 2,
        "unique_claim_count": 2,
        "fresh_evidence_count": 3,
        "deduplicated_evidence_count": 1,
        "stale_evidence_count": 0,
        "future_evidence_count": 0,
    }
    values.update(overrides)
    return CrossSourceScoreInput(**values)


def test_confirmed_source_score_is_eligible_and_explained():
    result = score_cross_source_confirmation(_input())
    assert result.eligible is True
    assert result.score == 81.0
    assert result.risk_score == 5.0
    assert result.breakdown["duplicate_penalty"] == 4.0
    assert len(result.input_signature) == 64


def test_unconfirmed_or_high_risk_source_score_is_suppressed():
    result = score_cross_source_confirmation(_input(confirmed=False, confirmation_status="INSUFFICIENT_EVIDENCE", future_evidence_count=2))
    assert result.eligible is False
    assert result.risk_score == 75.0
    assert "suppressed" in result.reasons[-1]


def test_score_signature_changes_with_policy_or_signal_state():
    first = score_cross_source_confirmation(_input())
    assert first.input_signature != score_cross_source_confirmation(_input(unique_claim_count=3)).input_signature
    assert first.input_signature != score_cross_source_confirmation(_input(), policy=CrossSourceScorePolicy(min_alert_score=85)).input_signature
