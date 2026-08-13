import hashlib
from datetime import datetime

from app.db.models import Keyword, NormalizedItem, Opportunity, OpportunityEvidence, RawObservation
from app.db.session import SessionLocal
from app.domain.digest import DigestEvidenceProvenance, DigestItem, DigestSelectionPolicy, DigestStatus
from app.services.digest import deduplicate_and_rank_digest_items, generate_daily_digest


def make_digest_item(rank: int, *, opportunity_id: int, opportunity_key: str, score: float) -> DigestItem:
    return DigestItem(
        rank=rank,
        opportunity_id=opportunity_id,
        opportunity_key=opportunity_key,
        title="Test opportunity",
        stage="DISCOVERY",
        score=score,
        risk_score=20,
        evidence_count=1,
        summary="synthetic digest test",
        analysis_status="READY",
        analysis_provider="heuristic",
        analysis_signature="a" * 64,
        last_seen_at=datetime(2026, 8, 12),
        evidence_ids=["ev1_" + "a" * 64],
        evidence_provenance=DigestEvidenceProvenance.SYNTHETIC,
        selection_reasons=["synthetic test candidate"],
    )


def test_digest_generation_deduplicates_by_stable_key_and_ranks_deterministically():
    policy = DigestSelectionPolicy(max_items=2)
    items = [
        make_digest_item(1, opportunity_id=1, opportunity_key="opp:a", score=70),
        make_digest_item(1, opportunity_id=2, opportunity_key="opp:a", score=80),
        make_digest_item(1, opportunity_id=3, opportunity_key="opp:b", score=75),
    ]
    ranked = deduplicate_and_rank_digest_items(items, policy=policy)
    assert [(item.rank, item.opportunity_id, item.opportunity_key) for item in ranked] == [(1, 2, "opp:a"), (2, 3, "opp:b")]


def test_generate_daily_digest_returns_empty_without_qualifying_data():
    with SessionLocal() as db:
        digest = generate_daily_digest(db, digest_date=datetime(2026, 8, 12).date())
    assert digest.status == DigestStatus.EMPTY
    assert digest.items == []
    assert digest.total_candidates == 0


def test_generate_daily_digest_contains_traceable_synthetic_evidence():
    with SessionLocal() as db:
        keyword = Keyword(canonical="digest-contract", display_name="Digest contract", status="ACTIVE", first_seen_at=datetime(2026, 8, 11), last_seen_at=datetime(2026, 8, 12), observation_count=1, source_count=1, score=80)
        db.add(keyword)
        db.flush()
        content_hash = hashlib.sha256(b"digest-synthetic-evidence").hexdigest()
        raw = RawObservation(source_id="digest-synthetic", external_id="1", query="digest", item_type="CONTENT", title="Synthetic evidence", text="SYNTHETIC evidence", observed_at=datetime(2026, 8, 12, 5), acquisition_method="MANUAL_IMPORT", evidence_quality="E", acquisition_risk="R2", content_hash=content_hash, raw_payload={"data_class": "SYNTHETIC"}, raw_payload_bytes=0)
        db.add(raw)
        db.flush()
        item = NormalizedItem(raw_observation_id=raw.id, canonical_key="digest-synthetic", source_id=raw.source_id, query=raw.query, item_type=raw.item_type, title=raw.title, text=raw.text, source_url=None, observed_at=raw.observed_at)
        db.add(item)
        db.flush()
        opportunity = Opportunity(opportunity_key="opp:digest-synthetic", keyword_id=keyword.id, title="Synthetic digest opportunity", stage="DISCOVERY", score=88, risk_score=12, evidence_count=1, last_seen_at=datetime(2026, 8, 12, 5), updated_at=datetime(2026, 8, 12, 5), analysis_provider="heuristic", analysis_status="READY", analysis_signature="a" * 64, score_breakdown={"model_version": "score-v1", "total": 88})
        db.add(opportunity)
        db.flush()
        db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", weight=0.25, observed_at=item.observed_at))
        db.commit()
        digest = generate_daily_digest(db, digest_date=datetime(2026, 8, 12).date())
    assert digest.status == DigestStatus.READY
    assert digest.items[0].evidence_provenance == DigestEvidenceProvenance.SYNTHETIC
    assert digest.items[0].evidence_ids == [f"ev1_{content_hash}"]
