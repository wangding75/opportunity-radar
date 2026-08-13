from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.models import (
    Keyword,
    NormalizedItem,
    Opportunity,
    OpportunityClusterVersion,
    OpportunityEvidence,
    OpportunityKeyword,
    OpportunityLineage,
    OpportunityScoreSnapshot,
    RawObservation,
)
from app.db.session import SessionLocal
from app.services.opportunity_score_lineage_audit import audit_opportunity_score_lineage
from app.services.scoring import ScoreInputs, calculate_score, record_score_snapshot


def _make_opportunity(db, suffix: str) -> Opportunity:
    now = datetime(2026, 8, 13, 2, 0)
    keyword = Keyword(
        canonical=f"synthetic-score-{suffix}",
        display_name=f"Synthetic score {suffix}",
        first_seen_at=now,
        last_seen_at=now,
        observation_count=3,
        source_count=2,
        score=10.0,
    )
    db.add(keyword)
    db.flush()
    raw = RawObservation(
        source_id=f"synthetic-score-source-{suffix}",
        external_id=f"raw-{suffix}",
        query="synthetic score lineage",
        item_type="TREND",
        title="synthetic score evidence",
        text="synthetic evidence",
        observed_at=now,
        acquisition_method="MANUAL_IMPORT",
        evidence_quality="C",
        acquisition_risk="R2",
        content_hash=hashlib.sha256(suffix.encode()).hexdigest(),
        raw_payload={"data_class": "SYNTHETIC"},
    )
    db.add(raw)
    db.flush()
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=hashlib.sha256(f"item-{suffix}".encode()).hexdigest(),
        source_id=raw.source_id,
        query=raw.query,
        item_type=raw.item_type,
        title=raw.title,
        text=raw.text,
        observed_at=now,
    )
    db.add(item)
    db.flush()
    inputs = ScoreInputs(1.0, 0.0, 0.0, 2, 1, 2, 1)
    score, breakdown = calculate_score(inputs)
    components = breakdown["components"]
    opportunity = Opportunity(
        opportunity_key=f"opp:synthetic-score-{suffix}",
        keyword_id=keyword.id,
        title=keyword.display_name,
        stage="DISCOVERY",
        score=score,
        demand_score=components["demand"],
        supply_score=components["supply"],
        execution_score=components["execution"],
        cross_source_score=components["cross_source"],
        saturation_score=components["saturation"],
        risk_score=10.0,
        evidence_count=1,
        first_seen_at=now,
        last_seen_at=now,
        updated_at=now,
        related_keyword_count=1,
        cluster_generation=1,
        cluster_signature=hashlib.sha256(str(keyword.id).encode()).hexdigest(),
        score_version="score-v1",
        score_breakdown=breakdown,
    )
    db.add(opportunity)
    db.flush()
    db.add(OpportunityKeyword(opportunity_id=opportunity.id, keyword_id=keyword.id, role="PRIMARY", weight=keyword.score))
    db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", weight=0.75, observed_at=now))
    db.add(OpportunityClusterVersion(
        opportunity_id=opportunity.id,
        generation=1,
        cluster_signature=opportunity.cluster_signature,
        keyword_ids=[keyword.id],
        change_type="CREATED",
        started_at=now,
    ))
    db.flush()
    assert record_score_snapshot(db, opportunity, now=now) is True
    db.flush()
    return opportunity


def test_empty_opportunity_score_lineage_audit_is_pass():
    with SessionLocal() as db:
        result = audit_opportunity_score_lineage(db)
        assert result["status"] == "PASS"
        assert result["summary"]["real_data_collected"] == 0


def test_opportunity_score_lineage_audit_accepts_complete_synthetic_chain_and_snapshot_retry_is_idempotent():
    with SessionLocal() as db:
        opportunity = _make_opportunity(db, "complete")
        assert record_score_snapshot(db, opportunity, now=datetime(2026, 8, 13, 2, 0) + timedelta(hours=1)) is False
        result = audit_opportunity_score_lineage(db)
        assert result["status"] == "PASS", result
        assert result["summary"]["score_snapshots"] == 1


def test_audit_detects_evidence_count_and_snapshot_signature_drift():
    with SessionLocal() as db:
        opportunity = _make_opportunity(db, "tamper")
        opportunity.evidence_count = 9
        snapshot = db.scalar(select(OpportunityScoreSnapshot))
        assert snapshot is not None
        snapshot.input_signature = "a" * 64
        db.flush()
        result = audit_opportunity_score_lineage(db)
        assert result["status"] == "FAIL"
        rules = {row["rule"] for row in result["violations"]}
        assert "opportunity_evidence_count_matches_rows" in rules
        assert "score_snapshot_signature_matches_payload" in rules


def test_audit_detects_lineage_cycle():
    with SessionLocal() as db:
        parent = _make_opportunity(db, "parent")
        child = _make_opportunity(db, "child")
        db.add(OpportunityLineage(parent_opportunity_id=parent.id, child_opportunity_id=child.id, relation_type="SPLIT_INTO"))
        db.add(OpportunityLineage(parent_opportunity_id=child.id, child_opportunity_id=parent.id, relation_type="SPLIT_INTO"))
        db.flush()
        result = audit_opportunity_score_lineage(db)
        assert result["status"] == "FAIL"
        assert any(row["rule"] == "lineage_is_acyclic" for row in result["violations"])
