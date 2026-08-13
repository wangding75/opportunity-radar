# MVP Baseline Validation Report

Date: 2026-08-12
Version: 0.1.0-mvp-baseline

## Scope

本轮覆盖 MVP 数据主链，不包含百度指数、闲鱼网页、招聘、抖音指数、微信指数的正式 Collector，也不包含模拟器 Hook 执行实现。

## Implemented

- Source Registry / Capability Contract
- Raw Observation Store
- Normalization Pipeline
- Keyword Registry / Candidate Discovery
- Keyword Metrics / Lifecycle
- Deterministic signal score baseline
- GitHub REST Search Connector
- JSON import
- Instrumented App Observation ingestion contract
- Dashboard API / MVP web UI
- Alembic migration

## Verification

- `pytest -q`: 5/5 PASS
- Python `compileall`: PASS
- Shell `bash -n`: PASS
- Alembic upgrade head: PASS
- Alembic downgrade base: PASS
- FastAPI startup smoke: PASS
- Sample import: PASS (2 inserted)
- Dashboard smoke: PASS
- Web index smoke: PASS

## Known limitations

1. Keyword discovery for Chinese currently uses deterministic phrase extraction; semantic clustering/LLM expansion is not implemented yet.
2. Signal score is an MVP heuristic; 7/30/90 day time-series tables and opportunity evidence graph are not yet implemented.
3. GitHub live API was not called during automated validation; connector parsing was tested against the official API response shape with `httpx.MockTransport`.
4. PostgreSQL schema is supported by SQLAlchemy/Alembic design but this environment did not run a real PostgreSQL server.
5. Instrumented App source only defines ingestion/provenance contracts. No authentication bypass, anti-bot bypass, paywall bypass, or private-data acquisition code exists.
