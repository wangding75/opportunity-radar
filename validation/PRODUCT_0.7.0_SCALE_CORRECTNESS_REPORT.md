# Opportunity Radar 0.7.0 Scale & Correctness Validation Report

Date: 2026-08-12
Status: PASS
Version: `0.7.0-scale-correctness`
Schema revision: `0007_scale_correctness`

## Scope

This release fixes the highest-priority non-data-source product issues identified in the 0.6.0 review. It does not claim that all complete-product work is finished.

Implemented in this release:

- Incremental derived analysis for changed observations/keywords/dates instead of mandatory full rebuild on every ingest.
- Bounded full-reconciliation maintenance path retained for drift correction.
- Stable Opportunity identity independent of `cluster:min(keyword_id)`.
- Opportunity cluster version history plus merge/split lineage.
- Research state preservation across automatic cluster merge/split.
- Keyword relation/source maintenance changed from pairwise N+1 history queries to set-based/bulk maintenance.
- Event-driven alert evaluation queue for changed Opportunities.
- Keyset/cursor pagination for Opportunity and Observation scale paths.
- PostgreSQL `pg_trgm` migration/index baseline for current ILIKE search paths.
- Dedicated one-shot migration service in Docker Compose; API and Worker no longer race Alembic on startup.
- Worker heartbeat/health reporting and stale-worker detection.
- Maintenance worker mode for periodic full reconciliation and retention execution.
- Retention framework for collection runs, audit logs and alert events.
- Raw research evidence remains deletion-protected until a cold-archive handoff exists.
- 0.6 -> 0.7 upgrade validation preserving Opportunity research data.

## Automated validation

- `pytest`: 61/61 PASS
- Python `compileall`: PASS
- Frontend JavaScript syntax check: PASS
- Shell syntax validation: PASS
- Docker Compose YAML structure validation: PASS
- `git diff --check`: PASS

## Database / migration validation

- SQLite `alembic upgrade head`: PASS
- Alembic model/schema consistency (`alembic check`): PASS
- SQLite `downgrade base -> upgrade head`: PASS
- PostgreSQL offline migration DDL generation: PASS
- 0.3 -> 0.4 migration: PASS
- 0.4 -> 0.5 migration: PASS
- 0.5 -> 0.6 migration: PASS
- 0.6 -> 0.7 migration: PASS
- SQLite backup -> mutation -> restore E2E: PASS

## Scale/correctness regression coverage

Dedicated 0.7 tests verify:

1. Incremental trend updates do not delete unrelated historical materializations.
2. Opportunity identity survives cluster merge.
3. Star/research note state remains attached after merge.
4. Merge lineage is persisted.
5. Relation source counts are maintained incrementally and de-duplicated.
6. Alert queue evaluates changed Opportunities rather than requiring a full scan.
7. Cursor pagination does not duplicate records between pages.
8. Worker heartbeat and retention preview are operational.
9. Incremental Opportunity refresh leaves unrelated cluster generation/timestamp untouched.
10. A 12-keyword / 66-pair relation update remains below the SQL statement guard (`<=12`) after bulk maintenance, replacing the prior 100+ statement path.

## Real HTTP / worker smoke

Fresh SQLite database was migrated to `0007_scale_correctness`, then a real Uvicorn process was started.

Validated:

- `/ready`: version `0.7.0`, schema revision `0007_scale_correctness`.
- HTTP import of three observations: PASS.
- Stable `opp:<uuid>` Opportunity produced: PASS.
- Opportunity keyset page endpoint: PASS.
- Observation cursor page endpoint: PASS.
- Retention dry-run endpoint: PASS.
- `maintenance --once` worker execution: PASS.
- Worker heartbeat persisted as IDLE with iteration count 1: PASS.

## Known validation limits

The current execution environment does not provide a running Docker daemon or a real PostgreSQL server. Therefore:

- Docker Compose configuration is parsed/validated but containers were not started here.
- PostgreSQL migration SQL is generated and driver/config support exists, but a real multi-process PostgreSQL E2E/concurrency test remains outstanding.

## Remaining non-data-source product work

These items are intentionally **not** marked complete by this release:

- User/session/RBAC authentication; current product still has single API-key mode and the static web client stores it in localStorage.
- Formal React + TypeScript front-end and browser E2E/accessibility suite.
- Scoring model versioning, replay, backtesting and false-positive feedback loop.
- Structured production logs, metrics/tracing and external operational alerting.
- API router modularization and comprehensive typed response schemas.
- Fully locked/reproducible dependency set and SBOM automation.
- Cold archive / partition lifecycle for raw evidence.
- Staged PostgreSQL disaster recovery validation and production RPO/RTO drills.
- Real PostgreSQL multi-instance concurrency/load testing.

## Conclusion

PASS for the 0.7.0 Scale & Correctness scope. The highest-priority scale/correctness defects identified in the 0.6 review have been fixed and protected by regression tests. Remaining work is explicitly tracked above and is not represented as complete.
