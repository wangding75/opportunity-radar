import hashlib
from datetime import datetime

from sqlalchemy import select

from app.db.models import Keyword, NormalizedItem, Opportunity, OpportunityEvidence, OpportunityScoreSnapshot, RawObservation, ScoreJumpRecord
from app.db.session import SessionLocal
from app.services.score_jumps import materialize_score_jumps


NOW = datetime(2026, 8, 12, 12)
PREVIOUS_AT = datetime(2026, 8, 1)
CURRENT_AT = datetime(2026, 8, 2)


def _raw(*, suffix: str, observed_at: datetime, title: str) -> RawObservation:
    text = f"SYNTHETIC score-jump evidence {suffix}"
    return RawObservation(
        source_id=f"synthetic-source-{suffix}",
        external_id=f"synthetic-{suffix}",
        query="synthetic score jump",
        item_type="NEWS",
        title=title,
        text=text,
        source_url=f"https://synthetic.invalid/{suffix}",
        observed_at=observed_at,
        acquisition_method="MOCK",
        evidence_quality="MEDIUM",
        acquisition_risk="LOW",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        raw_payload={"data_class": "SYNTHETIC"},
    )


def _seed(*, with_evidence: bool, boundary_only: bool = False) -> tuple[int, str | None]:
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-score-jump-breakdown", display_name="SYNTHETIC Score Jump Breakdown", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key="synthetic-score-jump-breakdown",
            keyword_id=keyword.id,
            title="SYNTHETIC score jump breakdown opportunity",
            stage="VALIDATED",
            score=60.0,
        )
        db.add(opportunity)
        db.flush()
        db.add(
            OpportunityScoreSnapshot(
                opportunity_id=opportunity.id,
                model_version="score-v1",
                input_signature="a" * 64,
                score=40.0,
                risk_score=20.0,
                stage="DISCOVERY",
                evidence_count=1,
                breakdown={"data_class": "SYNTHETIC", "demand": 10, "total": 40},
                calculated_at=PREVIOUS_AT,
            )
        )
        db.add(
            OpportunityScoreSnapshot(
                opportunity_id=opportunity.id,
                model_version="score-v1",
                input_signature="b" * 64,
                score=60.0,
                risk_score=15.0,
                stage="VALIDATED",
                evidence_count=2,
                breakdown={"data_class": "SYNTHETIC", "demand": 30, "total": 60},
                calculated_at=CURRENT_AT,
            )
        )
        evidence_id = None
        if with_evidence:
            observed_at = PREVIOUS_AT if boundary_only else datetime(2026, 8, 1, 12)
            raw = _raw(suffix="boundary" if boundary_only else "in-window", observed_at=observed_at, title="SYNTHETIC score jump source")
            db.add(raw)
            db.flush()
            item = NormalizedItem(
                raw_observation_id=raw.id,
                canonical_key=f"synthetic-score-jump-{raw.id}",
                source_id=raw.source_id,
                query=raw.query,
                item_type=raw.item_type,
                title=raw.title,
                text=raw.text,
                source_url=raw.source_url,
                observed_at=observed_at,
            )
            db.add(item)
            db.flush()
            db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", observed_at=observed_at))
            evidence_id = f"ev1_{raw.content_hash}"
        db.commit()
        return opportunity.id, evidence_id


def test_score_jump_breakdown_binds_snapshot_changes_and_synthetic_evidence_idempotently():
    opportunity_id, evidence_id = _seed(with_evidence=True)
    with SessionLocal() as db:
        first = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        second = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        row = db.scalar(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id == opportunity_id))

    assert first["created"] == 1
    assert second["duplicates"] == 1
    assert row is not None
    assert row.previous_breakdown["total"] == 40
    assert row.current_breakdown["total"] == 60
    assert row.change_breakdown == {
        "score_delta": 20.0,
        "relative_delta": 0.5,
        "risk_score_delta": -5.0,
        "evidence_count_delta": 1,
        "stage": {"before": "DISCOVERY", "after": "VALIDATED"},
        "model_version": {"before": "score-v1", "after": "score-v1"},
    }
    assert row.evidence_ids == [evidence_id]
    assert row.evidence[0]["provenance"] == "SYNTHETIC"
    assert row.evidence[0]["text"].startswith("SYNTHETIC")


def test_score_jump_evidence_window_is_exclusive_of_previous_snapshot_boundary():
    opportunity_id, evidence_id = _seed(with_evidence=True, boundary_only=True)
    with SessionLocal() as db:
        result = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        row = db.scalar(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id == opportunity_id))
    assert result["created"] == 1
    assert row is not None
    assert evidence_id not in row.evidence_ids
    assert row.evidence == []


def test_score_jump_without_evidence_does_not_fabricate_citations():
    opportunity_id, _ = _seed(with_evidence=False)
    with SessionLocal() as db:
        result = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        row = db.scalar(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id == opportunity_id))
    assert result["jumped"] == 1
    assert row is not None
    assert row.evidence_ids == []
    assert row.evidence == []
