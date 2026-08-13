# Opportunity Radar 0.6.0 Product Core Validation Report

## Conclusion

**PASS** for this product-core development increment.

The project is no longer evaluated as an MVP. This increment adds persistent research workflow, alerts, user watch topics, source runtime controls, authentication/audit, production deployment artifacts, backup/restore, and a multi-workspace product UI on top of the existing discovery/intelligence runtime.

This report does **not** claim the entire final product/data-source roadmap is complete.

## Baseline

- Version: `0.6.0-product-core`
- Schema head: `0006_product_workflow_alerts`
- Runtime: FastAPI + SQLAlchemy + Alembic
- Local DB: SQLite with foreign keys, WAL and busy timeout
- Production DB policy: PostgreSQL required

## Product capabilities completed in this increment

- Opportunity Research state: NEW / REVIEWING / TRACKING / DISMISSED / ARCHIVED.
- Star, priority, notes and tags persisted separately from derived Opportunity analysis.
- Watch Keywords for user-defined monitoring topics.
- Alert Rules and internal Alert Event Inbox with cooldown/idempotency.
- Runtime SourcePreference enable/disable integrated with active collection and probe planning.
- Observation search and paginated result envelope.
- Opportunity and Observation CSV export with spreadsheet-formula injection neutralization.
- API Key read/write authentication modes; production mode refuses disabled auth, short key and SQLite.
- Request ID and mutation AuditLog without request payload/API-key logging.
- Multi-workspace Web UI: dashboard, opportunities, alerts, watch keywords, sources, observations, operations/audit.
- Worker modes: all / collection / analysis / alerts.
- Docker Compose production baseline: PostgreSQL + API + Worker.
- SQLite online backup/restore with integrity check; PostgreSQL pg_dump/pg_restore support.
- Alembic migration `0006_product_workflow_alerts` and historical upgrade tests.

## Automated validation

- pytest: **53/53 PASS**
- Python compileall: PASS
- Shell syntax: PASS
- Frontend inline JavaScript `node --check`: PASS
- Docker Compose YAML structure: PASS
- SQLite Alembic upgrade head: PASS
- Alembic schema check: PASS
- SQLite downgrade base: PASS
- PostgreSQL offline DDL generation: PASS
- 0.3 -> 0.4 migration: PASS
- 0.4 -> 0.5 migration: PASS
- 0.5 -> 0.6 migration: PASS
- SQLite backup -> mutate -> restore E2E: PASS
- `git diff --check`: PASS

## Real HTTP smoke

Executed with a fresh SQLite database, `AUTH_MODE=write` and a real local Uvicorn process.

- `/health`: PASS
- `/ready`: PASS
- write without API Key -> HTTP 401: PASS
- write with API Key -> persistent Watch Keyword created: PASS
- read-back: PASS
- `X-Request-ID` response header: PASS
- `X-Content-Type-Options: nosniff`: PASS

## Explicitly unverified / incomplete

- No real PostgreSQL Server is installed in the execution environment. PostgreSQL schema is verified by offline DDL, driver/configuration code, and production policy, but **real PostgreSQL E2E remains pending**.
- Docker Engine / Docker Compose runtime is not installed in the execution environment. Compose YAML is structurally validated but **container startup E2E remains pending**.
- Real external Google Trends/GitHub requests are not part of this product-core validation.
- Xianyu public-product connector is not implemented yet.
- Baidu Index connector is not implemented yet.
- Recruitment-platform connector is not implemented yet.
- Douyin Index / WeChat Index connectors are not implemented yet.
- Google Trends Alpha API provider is not implemented yet.
- Android emulator real instrumentation/hook runtime is not implemented; only the authorized PUSH_ONLY observation contract exists.
- Production LLM/n8n credentials are not available; HTTP analysis protocol has been tested previously with a local deterministic endpoint, not production credentials.
- External alert channels are not implemented; current alerting is an internal Inbox.
- Multi-user RBAC/team collaboration and long-term retention/archival jobs remain future product work.

## Safety boundary

Instrumented App support remains limited to authorized research observations visible to the research account. The product does not implement authentication bypass, CAPTCHA bypass, device-risk-control evasion, paid-access bypass, private-data access, or bulk-account countermeasures.
