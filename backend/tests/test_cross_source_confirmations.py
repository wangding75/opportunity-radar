import hashlib
from datetime import datetime

from sqlalchemy import func, select

from app.db.models import CrossSourceConfirmationRecord, Keyword, NormalizedItem, Opportunity, OpportunityEvidence, RawObservation
from app.db.session import SessionLocal
from app.services.cross_source_confirmations import materialize_cross_source_confirmations


NOW = datetime(2026, 8, 12, 12)


def _seed_opportunity(*, with_evidence: bool = True, invalid_hash: bool = False) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical=f"synthetic-cross-source-{with_evidence}-{invalid_hash}", display_name="SYNTHETIC Cross Source", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key=f"synthetic-cross-source-{with_evidence}-{invalid_hash}",
            keyword_id=keyword.id,
            title="SYNTHETIC cross-source opportunity",
            stage="VALIDATED",
            score=82.0,
        )
        db.add(opportunity)
        db.flush()
        if with_evidence:
            rows = [
                ("synthetic-a", "Claim A", "Source A independent claim", "https://a.synthetic.invalid/jobs/1", "a"),
                ("synthetic-b", "Claim B", "Source B independent claim", "https://b.synthetic.invalid/jobs/2", "b"),
                ("synthetic-b", "Claim A", "Source A independent claim", "https://b.synthetic.invalid/jobs/3", "c"),
            ]
            for source, title, text, url, marker in rows:
                content_hash = f"invalid-{marker}" if invalid_hash else hashlib.sha256(marker.encode()).hexdigest()
                observed_at = NOW
                raw = RawObservation(
                    source_id=source,
                    external_id=f"synthetic-cross-{marker}",
                    query="synthetic cross source",
                    item_type="CONTENT",
                    title=title,
                    text=text,
                    source_url=url,
                    observed_at=observed_at,
                    acquisition_method="MANUAL_IMPORT",
                    evidence_quality="E",
                    acquisition_risk="R2",
                    content_hash=content_hash,
                    raw_payload={"data_class": "SYNTHETIC"},
                )
                db.add(raw)
                db.flush()
                item = NormalizedItem(
                    raw_observation_id=raw.id,
                    canonical_key=hashlib.sha256(f"item-{marker}".encode()).hexdigest(),
                    source_id=source,
                    query=raw.query,
                    item_type=raw.item_type,
                    title=title,
                    text=text,
                    source_url=url,
                    observed_at=observed_at,
                )
                db.add(item)
                db.flush()
                db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", observed_at=observed_at))
        db.commit()
        return opportunity.id


def test_source_independence_persists_deduplicated_evidence_and_is_idempotent():
    opportunity_id = _seed_opportunity()
    with SessionLocal() as db:
        first = materialize_cross_source_confirmations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        second = materialize_cross_source_confirmations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()

    assert first == {"rule": "CROSS_SOURCE_CONFIRMATION", "evaluated": 1, "confirmed": 1, "created": 1, "duplicates": 0, "no_evidence": 0, "insufficient": 0}
    assert second["created"] == 0
    assert second["duplicates"] == 1
    with SessionLocal() as db:
        row = db.scalar(select(CrossSourceConfirmationRecord).where(CrossSourceConfirmationRecord.opportunity_id == opportunity_id))
        assert row is not None
        assert row.status == "CONFIRMED"
        assert row.confirmed is True
        assert row.independent_source_count == 2
        assert row.unique_claim_count == 2
        assert row.deduplicated_evidence_count == 1
        assert len(row.evidence_ids) == 2
        assert row.evidence[0]["provenance"] == "SYNTHETIC"
        assert db.scalar(select(func.count(CrossSourceConfirmationRecord.id)).where(CrossSourceConfirmationRecord.opportunity_id == opportunity_id)) == 1


def test_empty_and_invalid_raw_evidence_are_persisted_fail_closed():
    empty_id = _seed_opportunity(with_evidence=False)
    invalid_id = _seed_opportunity(invalid_hash=True)
    with SessionLocal() as db:
        result = materialize_cross_source_confirmations(db, opportunity_ids={empty_id, invalid_id}, evaluated_at=NOW)
        db.commit()

    assert result["evaluated"] == 2
    assert result["confirmed"] == 0
    assert result["no_evidence"] == 2
    with SessionLocal() as db:
        rows = db.scalars(select(CrossSourceConfirmationRecord).where(CrossSourceConfirmationRecord.opportunity_id.in_([empty_id, invalid_id]))).all()
        assert {row.status for row in rows} == {"NO_EVIDENCE"}
        assert all(row.confirmed is False and row.evidence_ids == [] for row in rows)


def test_rollback_allows_confirmation_retry_without_duplicate_record():
    opportunity_id = _seed_opportunity()
    with SessionLocal() as db:
        first = materialize_cross_source_confirmations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        assert first["created"] == 1
        db.rollback()
        retry = materialize_cross_source_confirmations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()

    assert retry["created"] == 1
    with SessionLocal() as db:
        assert db.scalar(select(func.count(CrossSourceConfirmationRecord.id)).where(CrossSourceConfirmationRecord.opportunity_id == opportunity_id)) == 1
