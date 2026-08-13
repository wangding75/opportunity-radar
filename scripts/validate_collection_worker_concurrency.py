#!/usr/bin/env python3
"""Run a bounded synthetic PostgreSQL multi-worker collection check."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Lock

from sqlalchemy import func, select

from app.connectors.base import SourceConnector
from app.connectors.registry import SourceRegistry
from app.core.time import utc_now
from app.db.models import CollectionRun, Keyword, NormalizedItem, ProbeTask, RawObservation, SourceHealthState
from app.db.session import SessionLocal
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, ItemType, QueryMode
from app.domain.schemas import CollectedRecord, CollectionResult, CollectorQuery, SourceDescriptor
from app.services.probes import run_due_probe_tasks


WORKERS = 8
SOURCE_ID = "synthetic-collection-worker"
QUERY = "SYNTHETIC collection worker"
_collect_lock = Lock()
_collect_calls = 0


class SyntheticCollectionConnector(SourceConnector):
    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id=SOURCE_ID,
            display_name="Synthetic collection worker",
            acquisition_method=AcquisitionMethod.MANUAL_IMPORT,
            evidence_quality=EvidenceQuality.E,
            acquisition_risk=AcquisitionRisk.R2,
            capabilities={Capability.SEARCH, Capability.SEARCH_OBSERVATION},
            query_mode=QueryMode.KEYWORD,
        )

    def collect(self, query: CollectorQuery) -> CollectionResult:
        global _collect_calls
        with _collect_lock:
            _collect_calls += 1
        return CollectionResult(
            source_id=SOURCE_ID,
            query=query.query,
            records=[
                CollectedRecord(
                    external_id="synthetic-collection-record-1",
                    item_type=ItemType.CONTENT,
                    title="SYNTHETIC collection worker result",
                    text="SYNTHETIC collection worker evidence",
                    payload={"data_class": "SYNTHETIC"},
                )
            ],
        )


def _seed() -> int:
    now = utc_now()
    with SessionLocal() as db:
        keyword = Keyword(
            canonical="synthetic-collection-worker",
            display_name="SYNTHETIC collection worker",
            status="ACTIVE",
            score=50.0,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(keyword)
        db.flush()
        task = ProbeTask(
            source_id=SOURCE_ID,
            query=QUERY,
            intent="BASE",
            keyword_id=keyword.id,
            priority=100.0,
            interval_minutes=60,
            active=True,
            next_run_at=now - timedelta(minutes=1),
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        db.commit()
        return task.id


def _worker(index: int, barrier: Barrier, task_id: int) -> dict:
    barrier.wait()
    registry = SourceRegistry()
    registry.register(SyntheticCollectionConnector())
    try:
        with SessionLocal() as db:
            return run_due_probe_tasks(
                db,
                registry,
                limit=1,
                worker_id=f"synthetic-collection-worker-{index}",
            )
    finally:
        registry.close()


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        raise SystemExit("COLLECTION_CONCURRENCY_BLOCKED: DATABASE_URL must use PostgreSQL")
    task_id = _seed()
    barrier = Barrier(WORKERS)
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        results = list(executor.map(lambda index: _worker(index, barrier, task_id), range(WORKERS)))

    with SessionLocal() as db:
        task = db.get(ProbeTask, task_id)
        run_count = db.scalar(select(func.count(CollectionRun.id)).where(CollectionRun.probe_task_id == task_id)) or 0
        success_count = db.scalar(select(func.count(CollectionRun.id)).where(CollectionRun.probe_task_id == task_id, CollectionRun.status == "SUCCEEDED")) or 0
        raw_count = db.scalar(select(func.count(RawObservation.id)).where(RawObservation.source_id == SOURCE_ID)) or 0
        normalized_count = db.scalar(select(func.count(NormalizedItem.id)).where(NormalizedItem.source_id == SOURCE_ID)) or 0
        health = db.get(SourceHealthState, SOURCE_ID)

    claimed = sum(row["claimed"] for row in results)
    executed = sum(row["executed"] for row in results)
    if (
        claimed != 1
        or executed != 1
        or _collect_calls != 1
        or run_count != 1
        or success_count != 1
        or raw_count != 1
        or normalized_count != 1
        or task is None
        or task.lease_owner is not None
        or task.lease_until is not None
        or task.last_status != "SUCCEEDED"
        or health is None
        or health.total_runs != 1
    ):
        raise SystemExit(
            "COLLECTION_CONCURRENCY_FAIL: "
            f"claimed={claimed} executed={executed} collect_calls={_collect_calls} runs={run_count} "
            f"successes={success_count} raw={raw_count} normalized={normalized_count}"
        )
    if any(row.get("lease_lost") for result in results for row in result["results"]):
        raise SystemExit("COLLECTION_CONCURRENCY_FAIL: owner lost lease while finalizing")

    output = {
        "status": "PASS",
        "workers": WORKERS,
        "claimed": claimed,
        "executed": executed,
        "connector_calls": _collect_calls,
        "collection_runs": run_count,
        "raw_observations": raw_count,
        "normalized_items": normalized_count,
        "real_data_collected": 0,
        "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
    }
    print(f"COLLECTION_CONCURRENCY_PASS: workers={WORKERS} claimed=1 executed=1 connector_calls=1")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
