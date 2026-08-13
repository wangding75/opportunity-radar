from datetime import datetime
from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import Keyword, Opportunity, OpportunityScoreSnapshot, ScoreJumpRecord
from app.db.session import SessionLocal
from app.main import app
from app.services.score_jumps import materialize_score_jumps


client = TestClient(app)
NOW = datetime(2026, 8, 12, 12)


def _seed_history(*, with_previous: bool = True, version_mismatch: bool = False) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical=f"synthetic-score-jump-{with_previous}-{version_mismatch}", display_name="SYNTHETIC Score Jump", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key=f"synthetic-score-jump-{with_previous}-{version_mismatch}",
            keyword_id=keyword.id,
            title="SYNTHETIC score jump opportunity",
            stage="VALIDATED",
            score=70.0,
        )
        db.add(opportunity)
        db.flush()
        if with_previous:
            db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="a" * 64, score=40.0, risk_score=20.0, stage="DISCOVERY", evidence_count=2, breakdown={"data_class": "SYNTHETIC", "total": 40}, calculated_at=datetime(2026, 8, 1)))
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v2" if version_mismatch else "score-v1", input_signature="b" * 64, score=60.0, risk_score=15.0, stage="VALIDATED", evidence_count=4, breakdown={"data_class": "SYNTHETIC", "total": 60}, calculated_at=datetime(2026, 8, 2)))
        db.commit()
        return opportunity.id


def test_score_jump_materialization_persists_jump_and_is_idempotent():
    opportunity_id = _seed_history()
    with SessionLocal() as db:
        first = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        second = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()

    assert first == {"rule": "SCORE_JUMP", "evaluated": 1, "jumped": 1, "created": 1, "duplicates": 0, "no_baseline": 0, "suppressed": 0}
    assert second["created"] == 0
    assert second["duplicates"] == 1
    with SessionLocal() as db:
        row = db.scalar(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id == opportunity_id))
        assert row is not None
        assert row.status == "SCORE_JUMP"
        assert row.jumped is True
        assert row.absolute_delta == 20.0
        assert row.relative_delta == 0.5
        assert row.current_snapshot_signature == "b" * 64
        assert db.scalar(select(func.count(ScoreJumpRecord.id)).where(ScoreJumpRecord.opportunity_id == opportunity_id)) == 1

    response = client.get("/api/v1/scoring/score-jumps/records", params={"opportunity_id": opportunity_id})
    assert response.status_code == 200
    assert response.json()[0]["status"] == "SCORE_JUMP"


def test_score_jump_empty_baseline_and_version_mismatch_are_persisted_fail_closed():
    empty_id = _seed_history(with_previous=False)
    mismatch_id = _seed_history(version_mismatch=True)
    with SessionLocal() as db:
        result = materialize_score_jumps(db, opportunity_ids={empty_id, mismatch_id}, evaluated_at=NOW)
        db.commit()

    assert result["evaluated"] == 2
    assert result["jumped"] == 0
    assert result["no_baseline"] == 1
    assert result["suppressed"] == 1
    with SessionLocal() as db:
        rows = db.scalars(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id.in_([empty_id, mismatch_id]))).all()
        assert {row.status for row in rows} == {"NO_BASELINE", "VERSION_MISMATCH"}
        assert all(row.jumped is False for row in rows)


def test_score_jump_rollback_allows_retry_and_endpoint_requires_admin_in_rbac(monkeypatch):
    opportunity_id = _seed_history()
    with SessionLocal() as db:
        first = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        assert first["created"] == 1
        db.rollback()
        retry = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
    assert retry["created"] == 1

    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    assert client.post("/api/v1/scoring/score-jumps/evaluate").status_code == 401
