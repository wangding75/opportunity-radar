# Opportunity Radar 0.8.1 Global Review Report

Date: 2026-08-12
Base: `0.8.0-product-hardening` / `a69c45a3704520c62ddb5391c332fe6861a3a9e7`
Target: `0.8.1-global-review`
Schema revision: `0009_product_hardening` (no schema change required)

## Review conclusion

PASS for the implemented product scope after direct fixes. This review did not treat the existing 90-test green baseline as proof of correctness. It re-reviewed business correctness, cluster identity, scoring/backtest semantics, worker scheduling, transaction/concurrency boundaries, RBAC, input/output limits, external HTTP/XML handling, backup/restore, deployment defaults, UI reachability, observability and false-completion patterns.

No placeholder success path or newly introduced TODO/FIXME remains in the implemented business path. Abstract connector/analyzer `NotImplementedError` methods remain intentional extension contracts.

## Material defects fixed

### Opportunity and scoring correctness

- Stable Opportunity identity on split now follows strongest overlap instead of component iteration order.
- Pending `OpportunityLineage` rows are checked in-memory when SQLAlchemy `autoflush=False`, preventing same-transaction duplicate lineage insert failures.
- Large connected keyword components are never silently truncated; incremental refresh falls back to full reconciliation when its safety scope is exceeded.
- Limited reconciliation treats the limit as seed count and expands complete connected components, preventing unrelated opportunities from being incorrectly marked DORMANT.
- Opportunity cluster membership is no longer truncated by the external-analysis keyword payload cap.
- Opportunity refresh queries only recent 90-day evidence into memory while preserving historical first-seen time through SQL aggregation.
- Backtest evaluates mature threshold crossings only; recent signals are reported as immature instead of failures.
- Backtest now loads the exact last score state before the lookback window, eliminating false crossings when an unchanged high state is older than a fixed warm-up interval.
- Production now runs recurring full maintenance so time decay / relation expiry / DORMANT convergence does not depend on new observations arriving.

### Concurrency and worker reliability

- Probe claim lease is longer than stale collection recovery, preventing a valid long-running collection from being re-claimed by another worker.
- Stale collection recovery updates the linked ProbeTask failure/backoff state.
- Analysis HTTP timeout is validated against worker stale thresholds.
- Maintenance uses its own stale threshold and long idle sleeps refresh heartbeat.
- Queue processors expose progress callbacks; PostgreSQL can persist progress heartbeat during long work without committing business transactions.
- SQLite avoids concurrent progress-heartbeat writes while a maintenance write transaction is open, preventing `database is locked` regressions.
- PostgreSQL failed-login counters are serialized with row locking.
- Manual Alert evaluation and worker Alert evaluation share a PostgreSQL advisory transaction lock.
- Alert queue revision/claim/backoff semantics prevent duplicate processing, stale revision completion and failure hot loops.

### RBAC and product security

- RESEARCHER can no longer inject manual/imported or Instrumented App evidence that changes keyword/opportunity scores; ingestion is ADMIN-only.
- Operational ProbeTask and CollectionRun endpoints are ADMIN-only.
- Non-admin Source Health responses redact connector internal `last_error` details.
- Global/manual Alert evaluation and pending-queue execution are ADMIN operations; creating/updating alert rules remains a RESEARCHER workflow and already queues affected opportunities automatically.
- Expired sessions fail CSRF validation.
- Production external structured-analysis endpoints must use HTTPS.
- Instrumented App sanitizer strips URL userinfo and common API-key/session/credential fields, including camelCase variants.
- Observation payloads must be genuinely JSON-serializable before ingestion.
- Request bodies have an ASGI-level hard size ceiling, including chunked bodies without Content-Length.
- Per-observation, aggregate-import, payload-depth and payload-node limits prevent storage/recursive amplification.
- External Analysis, configured RSS/Atom, Google Trends RSS and GitHub HTTP responses use streaming byte ceilings instead of post-download size checks.
- Feed XML rejects DOCTYPE/ENTITY declarations before ElementTree parsing.

### Deployment, backup and recovery

- Production Compose no longer embeds `${POSTGRES_PASSWORD}` in SQLAlchemy URLs; password is supplied through `PGPASSWORD`, so reserved URL characters cannot break connection parsing.
- Recurring `worker-maintenance` is part of default production Compose; one-shot maintenance profile remains available.
- PostgreSQL backup verifies the custom archive with `pg_restore --list` before atomic rename.
- Staged PostgreSQL restore validates the archive and generated staging DB name; derived database names are capped to PostgreSQL identifier limits.
- Existing password-out-of-argv protection remains intact.

### Product/UI completeness

- Opportunity and Observation cursor APIs are connected to UI “load more” flows instead of silently exposing only the first 50/200 rows.
- Opportunity cursor paging preserves research-state/starred filters.
- Password reset is accessible from the user-management UI; backend revocation of sessions/tokens is retained.
- ADMIN no longer receives misleading edit/password controls for OWNER rows it cannot legally modify.
- “Immediate alert evaluation” is shown only to ADMIN/OWNER.

### Validation/tooling defects fixed

- `validate_product.sh` now validates the recurring maintenance service and password-safe PostgreSQL Compose configuration.
- Its quoted heredoc no longer expands `${POSTGRES_PASSWORD}` under `set -u`.
- Independent historical upgrade tests run in parallel, reducing full validation runtime without dropping checks.
- The real RBAC HTTP validation now confirms RESEARCHER cannot import evidence, force global alert evaluation, read worker/probe/collection operational endpoints, or access user administration.

## Validation evidence

- `pytest`: **115 / 115 PASS**
- Application line coverage: **86.08%**
  - statements: 4,375
  - covered: 3,766
  - missing: 609
- Strict TypeScript: PASS (`strict=true`, `noImplicitAny=true`)
- Frontend build + generated JavaScript syntax: PASS
- Static browser credential scan: PASS (no localStorage credential use; no inline executable JS)
- Python compileall: PASS
- Shell syntax: PASS
- Docker Compose YAML and service assertions: PASS
- OpenAPI: **52 paths / 56 operations**, duplicate operation IDs: 0
- `git diff --check`: PASS
- Supply-chain lock/SBOM fingerprint validation: PASS
- Fresh SQLite Alembic upgrade: PASS
- Alembic ORM/schema check: PASS (`No new upgrade operations detected`)
- Full downgrade-to-base / re-upgrade: PASS
- PostgreSQL offline DDL generation: PASS
- 0.3 -> 0.4 upgrade: PASS
- 0.4 -> 0.5 upgrade: PASS
- 0.5 -> 0.6 upgrade: PASS
- 0.6 -> 0.7 upgrade: PASS
- 0.7.0 -> 0.7.1 upgrade: PASS
- 0.7.1 -> 0.8.0/0.8.1 schema upgrade path: PASS (schema remains 0009)
- SQLite backup / mutate / restore E2E: PASS
- Real Uvicorn RBAC HTTP E2E: PASS
- Full `./scripts/validate_product.sh`: **PASS**, 34.3 seconds in the review environment

## Browser E2E boundary

`python scripts/validate_browser_e2e.py` was executed. Database migration and service startup succeeded, but Chromium navigation is blocked by the managed environment policy and returns:

`net::ERR_BLOCKED_BY_ADMINISTRATOR`

Therefore browser Playwright E2E is **environment-blocked and is not counted as PASS**. Strict TypeScript, frontend build/static checks and real HTTP RBAC E2E remain PASS.

## Environment / production boundaries not falsely marked complete

- No real PostgreSQL Server is available in this environment, so PostgreSQL multi-worker concurrency, advisory-lock behavior, `pg_trgm` extension privilege and staged restore promotion are not real-server E2E validated. SQL generation, CLI construction and deterministic tests pass.
- No Docker/Podman runtime is available here; Compose is parsed/validated but containers are not launched.
- Production LLM/n8n endpoint with real credentials is not connected.
- Full OpenTelemetry/OTLP distributed trace export is not implemented; current product has structured JSON logs, request/trace correlation IDs and metrics.
- Frontend remains strict TypeScript modules + static HTML; it has not been migrated to React.
- Some historical APIs still use hand-built response dictionaries rather than complete Pydantic response models.
- RawObservation PostgreSQL table partitioning is not implemented; payload cold archive is implemented.
- Public-internet login protection remains account-lock based; there is no distributed IP/global login rate limiter yet.

## Quality assessment

- Correctness: 9.2 / 10
- Test quality: 9.1 / 10
- Concurrency/reliability: 9.0 / 10 for implemented contracts, with real PostgreSQL E2E still pending
- Security: 9.0 / 10 for current single-workspace product boundary
- Maintainability: 8.6 / 10
- Observability/operations: 8.7 / 10
- Production readiness: 8.5 / 10

Overall code quality: **8.9 / 10**.

The largest remaining quality limitation is not an identified local correctness bug; it is lack of real PostgreSQL multi-process E2E and browser E2E in the current execution environment.
