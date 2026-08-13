from __future__ import annotations

from pathlib import Path


def test_postgres_concurrency_compose_is_static_and_health_gated():
    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.concurrency.yml").read_text(encoding="utf-8")
    runner = (root / "scripts" / "validate_postgres_runtime_e2e.py").read_text(encoding="utf-8")
    assert "postgres:17-alpine" in compose
    assert "condition: service_healthy" in compose
    assert "DATABASE_URL: postgresql+psycopg://" in compose
    assert "opportunity_radar_concurrency_pgdata" in compose
    assert "command: [\"python\", \"scripts/validate_postgres_runtime_e2e.py\"]" in compose
    assert "_migrate(root)" in runner
    assert "owner_invariant" in runner
    assert "exclusive_task_claim" in runner
    assert "queue_idempotency" in runner
    assert "connection_recovery" in runner
