from __future__ import annotations

from pathlib import Path


def test_collection_worker_concurrency_contract_is_postgres_health_gated_and_synthetic():
    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.collection-concurrency.yml").read_text(encoding="utf-8")
    runner = (root / "scripts" / "validate_collection_worker_concurrency.py").read_text(encoding="utf-8")
    assert "postgres:17-alpine" in compose
    assert "condition: service_healthy" in compose
    assert "DATABASE_URL: postgresql+psycopg://" in compose
    assert "opportunity_radar_collection_concurrency_pgdata" in compose
    assert "WORKERS = 8" in runner and "ThreadPoolExecutor" in runner
    assert "SYNTHETIC" in runner and "COLLECTION_CONCURRENCY_PASS" in runner
    assert "run_due_probe_tasks" in runner and "connector_calls=1" in runner
