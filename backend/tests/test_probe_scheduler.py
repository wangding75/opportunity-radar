from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.connectors.base import SourceConnector
from app.connectors.registry import SourceRegistry
from app.core.time import utc_now
from app.db.models import CollectionRun, ProbeTask
from app.db.session import SessionLocal
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, ItemType, QueryMode
from app.domain.schemas import CollectedRecord, CollectionResult, CollectorQuery, SourceDescriptor
from app.services.probes import _claim_due_task, _release_task_claim, run_due_probe_tasks, sync_probe_tasks


class FakeSearchConnector(SourceConnector):
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    @property
    def descriptor(self):
        return SourceDescriptor(
            source_id="fake_search",
            display_name="Fake Search",
            acquisition_method=AcquisitionMethod.OFFICIAL_API,
            evidence_quality=EvidenceQuality.A,
            acquisition_risk=AcquisitionRisk.R0,
            capabilities={Capability.SEARCH, Capability.PRODUCT, Capability.JOB, Capability.TREND},
            query_mode=QueryMode.KEYWORD,
        )

    def collect(self, query: CollectorQuery):
        if self.fail:
            raise RuntimeError("simulated source outage")
        return CollectionResult(
            source_id=self.descriptor.source_id,
            query=query.query,
            records=[
                CollectedRecord(
                    external_id=f"fake:{query.query}",
                    item_type=ItemType.CONTENT,
                    title=query.query,
                    text="自动化 工具 变现",
                    payload={"metric": 1},
                )
            ],
        )


def _seed_keyword():
    from app.main import app
    from fastapi.testclient import TestClient

    response = TestClient(app).post(
        "/api/v1/import",
        json={"records": [
            {"source_id": "seed_a", "query": "AI机会雷达", "external_id": "a", "item_type": "PRODUCT", "title": "AI机会雷达 工具"},
            {"source_id": "seed_b", "query": "AI机会雷达", "external_id": "b", "item_type": "JOB", "title": "AI机会雷达 运营招聘"},
            {"source_id": "seed_c", "query": "AI机会雷达", "external_id": "c", "item_type": "TREND", "title": "AI机会雷达 搜索增长"},
        ]},
    )
    assert response.status_code == 200


def test_probe_plan_is_persisted_and_due_task_executes_with_run_history():
    _seed_keyword()
    registry = SourceRegistry()
    registry.register(FakeSearchConnector())

    with SessionLocal() as db:
        sync = sync_probe_tasks(db, registry, keyword_limit=10, max_queries=10)
        assert sync["created"] > 0
        task = db.scalar(select(ProbeTask).where(ProbeTask.active.is_(True)))
        assert task is not None
        task.next_run_at = utc_now() - timedelta(minutes=1)
        db.commit()

        result = run_due_probe_tasks(db, registry, limit=1)
        assert result["executed"] == 1
        assert result["results"][0]["status"] == "SUCCEEDED"
        refreshed = db.get(ProbeTask, task.id)
        assert refreshed.last_status == "SUCCEEDED"
        assert refreshed.failure_count == 0
        assert refreshed.next_run_at > utc_now()
        run = db.scalar(select(CollectionRun).where(CollectionRun.probe_task_id == task.id))
        assert run is not None
        assert run.status == "SUCCEEDED"
        assert run.fetched == 1
        assert run.worker_id.startswith("collection-worker:")
        assert refreshed.lease_owner is None and refreshed.lease_until is None


def test_failed_probe_is_recorded_and_backed_off():
    _seed_keyword()
    registry = SourceRegistry()
    registry.register(FakeSearchConnector(fail=True))

    with SessionLocal() as db:
        sync_probe_tasks(db, registry, keyword_limit=10, max_queries=5)
        task = db.scalar(select(ProbeTask).where(ProbeTask.active.is_(True)))
        assert task is not None
        task.next_run_at = utc_now() - timedelta(minutes=1)
        db.commit()

        before = utc_now()
        result = run_due_probe_tasks(db, registry, limit=1)
        assert result["results"][0]["status"] == "FAILED"
        refreshed = db.get(ProbeTask, task.id)
        assert refreshed.failure_count == 1
        assert refreshed.last_status == "FAILED"
        assert refreshed.next_run_at >= before + timedelta(minutes=14)
        run = db.scalar(select(CollectionRun).where(CollectionRun.probe_task_id == task.id))
        assert run is not None
        assert run.status == "FAILED"
        assert "simulated source outage" in (run.error or "")


def test_stale_running_collection_run_is_recovered():
    from app.domain.enums import CollectionRunStatus

    registry = SourceRegistry()
    registry.register(FakeSearchConnector())
    with SessionLocal() as db:
        stale = CollectionRun(
            source_id="fake_search",
            query="old probe",
            status=CollectionRunStatus.RUNNING.value,
            started_at=utc_now() - timedelta(minutes=31),
        )
        db.add(stale)
        db.commit()
        result = run_due_probe_tasks(db, registry, limit=1)
        assert result["recovered_stale_runs"] == 1
        recovered = db.get(CollectionRun, stale.id)
        assert recovered.status == "FAILED"
        assert "interrupted" in (recovered.error or "")


def test_probe_progress_callback_runs_after_each_attempt():
    _seed_keyword()
    registry = SourceRegistry()
    registry.register(FakeSearchConnector())
    callbacks: list[str] = []
    with SessionLocal() as db:
        sync_probe_tasks(db, registry, keyword_limit=10, max_queries=5)
        task = db.scalar(select(ProbeTask).where(ProbeTask.active.is_(True)))
        assert task is not None
        task.next_run_at = utc_now() - timedelta(minutes=1)
        db.commit()
        result = run_due_probe_tasks(db, registry, limit=1, progress_callback=lambda: callbacks.append("beat"))
        assert result["executed"] == 1
        assert callbacks == ["beat"]


def test_collection_lease_is_exclusive_and_expired_lease_is_reclaimable():
    now = utc_now()
    with SessionLocal() as db:
        task = ProbeTask(
            source_id="synthetic-lease",
            query="SYNTHETIC lease",
            intent="BASE",
            priority=1,
            interval_minutes=60,
            active=True,
            next_run_at=now - timedelta(minutes=1),
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        db.commit()

        assert _claim_due_task(db, task.id, now=now, worker_id="worker-a") is True
        db.refresh(task)
        assert task.lease_owner == "worker-a" and task.lease_until is not None
        assert _claim_due_task(db, task.id, now=now, worker_id="worker-b") is False

        task.lease_until = now - timedelta(seconds=1)
        db.commit()
        assert _claim_due_task(db, task.id, now=now, worker_id="worker-b") is True
        db.refresh(task)
        assert task.lease_owner == "worker-b"
        assert _release_task_claim(
            db,
            task.id,
            worker_id="worker-a",
            next_run_at=now,
            last_run_at=now,
            last_status="FAILED",
            failure_count=99,
            last_error="stale worker must not overwrite",
            updated_at=now,
        ) is False
        db.refresh(task)
        assert task.lease_owner == "worker-b" and task.failure_count == 0
