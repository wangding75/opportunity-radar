from __future__ import annotations

from pathlib import Path


def test_postgres_concurrency_compose_contract_is_isolated_and_health_gated():
    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.concurrency.yml").read_text(encoding="utf-8")
    runner = (root / "scripts" / "validate_postgres_concurrency.py").read_text(encoding="utf-8")
    assert "postgres:17-alpine" in compose
    assert "condition: service_healthy" in compose
    assert "DATABASE_URL: postgresql+psycopg://" in compose
    assert "opportunity_radar_concurrency_pgdata" in compose
    assert "SYNTHETIC" in runner and "WORKERS = 8" in runner
    assert "ThreadPoolExecutor" in runner and "score_jumps=1" in runner
