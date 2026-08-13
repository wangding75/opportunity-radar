# Operations

## Production baseline

生产运行要求 PostgreSQL，并使用 RBAC Session / Personal API Token 鉴权。SQLite 只用于本地研究和开发。

```text
APP_ENV=production
AUTH_MODE=rbac
ALLOW_LEGACY_API_KEY=false
DATABASE_URL=postgresql+psycopg://...
```

## Processes

Migration 必须由独立 Job 单次执行，然后再启动 API/Worker：

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

首次生产部署创建 OWNER：

```bash
python -m app.admin_cli create-user owner --role OWNER
```

本地可使用组合 Worker：

```bash
python -m app.worker --mode all --interval 60
```

生产 Compose 默认拆成 Collection / Analysis / Alert / Maintenance 四类 Worker，避免外部采集或模型延迟阻塞预警，并保证随时间衰减的 Opportunity 会周期性全量纠偏：

```bash
python -m app.worker --mode collection --interval 60
python -m app.worker --mode analysis --interval 30 --no-sync
python -m app.worker --mode alerts --interval 30 --no-sync
python -m app.worker --mode maintenance --interval 21600 --no-sync
```

数据库 claim 负责避免同一 Probe / Analysis 被并发重复执行。

## Readiness

- `/health`：进程存活。
- `/ready`：数据库可连接、必须表存在、Alembic revision 与代码精确一致。

## Backup

```bash
python scripts/backup_database.py --output-dir backups
```

SQLite 备份执行完整性检查。PostgreSQL 需要系统安装 `pg_dump`。

## Restore

```bash
python scripts/restore_database.py <backup> --confirm-restore
```

PostgreSQL CLI 默认恢复到 staging database，验证 Revision/关键表后停止；使用 `--promote-staging` 才会显式切换。生产切换前仍应停止 API/Worker 或进入维护模式，避免目标数据库重命名期间新连接竞态。`--unsafe-in-place` 为明确的破坏性兼容路径。

## Source incident

数据源连续失败进入 DEGRADED，达到阈值进入 CIRCUIT_OPEN。限流错误可按 Retry-After 直接打开 Circuit。可从“数据源”工作区手工暂停来源。

## Audit

`/api/*` 非 GET/HEAD/OPTIONS 请求会写入 `audit_logs`，记录 Request ID、Actor、HTTP 方法、资源、状态码，不记录请求正文或 API Key。审计使用独立事务；若业务写已提交但审计落库失败，系统不会把成功写操作伪装成失败重试，而会记录服务器 ERROR 日志。因此当前审计链属于 best-effort，尚未达到独立不可抵赖审计存储。

## 0.7 production operations

### Migration ownership

Production Compose uses a one-shot `migrate` service. API and Worker containers wait for successful migration completion and do not run Alembic themselves. This removes multi-container migration races during cold starts and rolling restarts.

### Worker heartbeat

`worker_heartbeats` records worker identity, mode, status, last heartbeat, last successful iteration and iteration count. `/api/v1/workers` marks heartbeats stale according to `WORKER_STALE_SECONDS`.

### Maintenance worker

Production Compose runs a recurring `worker-maintenance` service for full reconciliation, retention, archive and auth cleanup. For an explicit one-shot maintenance run:

```bash
docker compose --profile maintenance run --rm maintenance
```

Normal collection/analysis/alert workers use incremental processing and should not run full reconciliation per ingestion. Maintenance uses its own stale threshold and emits progress heartbeats during long opportunity materialization.

### Retention

CollectionRun, AuditLog and AlertEvent retention are configurable. RawObservation remains protected from destructive deletion. Its raw payload body can be cold-archived independently to gzip JSONL with SHA-256 while the primary observation/evidence row remains online. Expired/revoked session and API-token records are also cleaned by maintenance according to `AUTH_RECORD_RETENTION_DAYS`.


## 0.8 authentication and observability

- Web clients authenticate with HttpOnly Session Cookie and CSRF protection.
- Personal API Tokens are hashed at rest; effective scopes are intersected with the user’s current role.
- Five failed login attempts lock an account temporarily; password reset revokes active sessions and personal tokens.
- `/metrics` requires read authorization and exposes process request metrics plus database-backed queue, stale-worker and open-circuit gauges.
- Application logs are structured JSON and include request/trace correlation IDs.
- Browser Playwright E2E is available as `REQUIRE_BROWSER_E2E=1 ./scripts/validate_product.sh`; the current validation container blocks browser navigation by managed Chromium policy, so that check is not counted as passed here.
