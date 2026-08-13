#!/usr/bin/env python3
"""Run a bounded synthetic PostgreSQL concurrency/idempotency check."""

from __future__ import annotations

import json
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from sqlalchemy import func, select

from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, Keyword, NormalizedItem, Opportunity, OpportunityEvidence, OpportunityScoreSnapshot, RawObservation, ScoreJumpRecord
from app.db.session import SessionLocal
from app.services.score_jump_alerts import materialize_score_jump_alerts
from app.services.score_jumps import materialize_score_jumps


WORKERS = 8


def _seed() -> tuple[int, int]:
    now = utc_now()
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-postgres-concurrency", display_name="Synthetic PostgreSQL concurrency", status="ACTIVE", first_seen_at=now, last_seen_at=now)
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key="opp:synthetic-postgres-concurrency",
            keyword_id=keyword.id,
            title="Synthetic PostgreSQL concurrency opportunity",
            stage="VALIDATED",
            score=70.0,
            risk_score=10.0,
            evidence_count=2,
        )
        db.add(opportunity)
        db.flush()
        evidence_at = now - timedelta(hours=12)
        evidence_text = "SYNTHETIC PostgreSQL concurrency evidence"
        raw = RawObservation(
            source_id="synthetic-postgres-concurrency-source",
            external_id="synthetic-postgres-concurrency-evidence",
            query="synthetic postgres concurrency",
            item_type="NEWS",
            title="Synthetic PostgreSQL concurrency evidence",
            text=evidence_text,
            observed_at=evidence_at,
            acquisition_method="MOCK",
            evidence_quality="C",
            acquisition_risk="R2",
            content_hash=hashlib.sha256(evidence_text.encode()).hexdigest(),
            raw_payload={"data_class": "SYNTHETIC"},
        )
        db.add(raw)
        db.flush()
        item = NormalizedItem(
            raw_observation_id=raw.id,
            canonical_key=hashlib.sha256(b"synthetic-postgres-concurrency-item").hexdigest(),
            source_id=raw.source_id,
            query=raw.query,
            item_type=raw.item_type,
            title=raw.title,
            text=raw.text,
            observed_at=evidence_at,
        )
        db.add(item)
        db.flush()
        db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="DEMAND", observed_at=evidence_at))
        db.add_all([
            OpportunityScoreSnapshot(
                opportunity_id=opportunity.id,
                model_version="score-v1",
                input_signature="a" * 64,
                score=40.0,
                risk_score=10.0,
                stage="DISCOVERY",
                evidence_count=1,
                breakdown={"data_class": "SYNTHETIC", "total": 40},
                calculated_at=now - timedelta(days=2),
            ),
            OpportunityScoreSnapshot(
                opportunity_id=opportunity.id,
                model_version="score-v1",
                input_signature="b" * 64,
                score=70.0,
                risk_score=10.0,
                stage="VALIDATED",
                evidence_count=2,
                breakdown={"data_class": "SYNTHETIC", "total": 70},
                calculated_at=now - timedelta(hours=1),
            ),
        ])
        db.add(AlertRule(
            name="SYNTHETIC_POSTGRES_CONCURRENCY",
            enabled=True,
            min_score=0.0,
            max_risk_score=100.0,
            min_evidence_count=1,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=0,
            created_at=now,
            updated_at=now,
        ))
        db.commit()
        return opportunity.id, keyword.id


def _worker(opportunity_id: int, barrier: Barrier) -> dict:
    barrier.wait()
    with SessionLocal() as db:
        try:
            jumps = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=utc_now())
            alerts = materialize_score_jump_alerts(db, opportunity_ids={opportunity_id})
            db.commit()
            return {"jumps": jumps, "alerts": alerts, "status": "COMMITTED"}
        except Exception:
            db.rollback()
            raise


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        raise SystemExit("POSTGRES_CONCURRENCY_BLOCKED: DATABASE_URL must use PostgreSQL")
    opportunity_id, _keyword_id = _seed()
    barrier = Barrier(WORKERS)
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        results = list(executor.map(lambda _: _worker(opportunity_id, barrier), range(WORKERS)))
    with SessionLocal() as db:
        score_jump_count = db.scalar(select(func.count(ScoreJumpRecord.id)).where(ScoreJumpRecord.opportunity_id == opportunity_id)) or 0
        event_count = db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.opportunity_id == opportunity_id)) or 0
        snapshot_count = db.scalar(select(func.count(OpportunityScoreSnapshot.id)).where(OpportunityScoreSnapshot.opportunity_id == opportunity_id)) or 0
    if score_jump_count != 1 or event_count != 1 or snapshot_count != 2:
        raise SystemExit(f"POSTGRES_CONCURRENCY_FAIL: score_jumps={score_jump_count} events={event_count} snapshots={snapshot_count}")
    if any(row["status"] != "COMMITTED" for row in results):
        raise SystemExit("POSTGRES_CONCURRENCY_FAIL: not all workers committed")
    output = {
        "status": "PASS",
        "workers": WORKERS,
        "score_jump_records": score_jump_count,
        "alert_events": event_count,
        "score_snapshots": snapshot_count,
        "real_data_collected": 0,
        "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
    }
    print(f"POSTGRES_CONCURRENCY_PASS: workers={WORKERS} score_jumps=1 alert_events=1")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
