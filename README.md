# Opportunity Radar

个人研究用信息差信号与商业机会发现系统。当前开发阶段已经切换到**完整产品标准**，不再以 MVP 为交付边界。

核心链路：

`Source -> Observation -> Keyword Discovery -> Trend/Graph -> Opportunity Cluster -> Structured Analysis -> Research Workflow -> Alert Inbox`

后台运行链路：

`Watch Keyword / Planner -> Persistent Probe -> CollectionRun -> Source Health -> Analysis Queue -> Alert Evaluation`

## 0.8.1 Global Review Fixes

0.8.1 is a global correctness/security review release. It fixes opportunity split identity selection, exact backtest threshold-crossing history, periodic maintenance/decay, worker leases and heartbeats, alert concurrency, RBAC evidence-ingestion boundaries, bounded external HTTP/XML parsing, recent-evidence query scaling, production PostgreSQL password handling, sanitizer credential leakage, and product pagination/admin UX gaps. Production Compose now includes a recurring maintenance worker by default.

## 0.8.0 Product Hardening

0.8.0 closes the highest-priority non-data-source product gaps from the 0.7.1 review:

- Multi-user RBAC with OWNER / ADMIN / RESEARCHER / VIEWER roles.
- HttpOnly session cookies + CSRF protection; browser credentials are no longer stored in `localStorage`.
- Personal API tokens whose effective permissions are capped by the user’s current role.
- Login failure lockout, password-reset session/token revocation, and maintenance cleanup for expired/revoked auth records.
- TypeScript frontend modules and an authenticated user-management workspace.
- Versioned opportunity scoring, persisted score snapshots, replay, and baseline backtest endpoints.
- Raw payload cold archive/restore using gzip JSONL + SHA-256 while retaining the primary Observation evidence row.
- PostgreSQL staged restore with archive preflight and explicit promotion; in-place destructive restore is no longer the CLI default.
- Structured JSON logging, request/trace correlation IDs, authenticated metrics, queue/worker/source-health gauges.
- Exact production/development dependency locks and a CycloneDX SBOM validated by dependency fingerprint.
- API routers split into auth/research/operations/scoring modules to reduce the former monolithic route file.

## 0.7.0 Scale & Correctness

### 增量分析与性能

- 新 Observation 不再触发全库派生数据重算；只刷新受影响 Keyword、Observed Day 和强关系闭包内 Opportunity。
- 保留显式 Full Reconciliation 维护模式，用于周期性纠偏、关系过期与 DORMANT 收敛。
- KeywordRelation 改为 set-based 批量读写，并新增 KeywordRelationSource，避免每个关键词 pair 历史回扫。
- 12 关键词 / 66 pair 场景增加 SQL 数量守卫，防止 N+1 回归。
- Alert 改为 Opportunity Change Queue 驱动，Worker 只评估变化 Opportunity；手工全量评估仍保留。

### 稳定 Opportunity Identity

- Opportunity Key 从 0.7 起视为稳定身份，不再随 cluster root keyword 改写。
- 新增 cluster signature / generation。
- 新增 OpportunityClusterVersion，保存聚类版本历史。
- 新增 OpportunityLineage，记录 MERGED_INTO / SPLIT_INTO。
- 聚类合并时优先保留有收藏、跟踪、优先级等人工研究状态的历史 Opportunity。
- Opportunity Detail 返回 cluster versions 与 lineage，研究记录不会因聚类重组丢失。

### 数据库与运行时

- PostgreSQL 增加 `pg_trgm` 搜索索引，现有 ILIKE 查询可使用 Trigram GIN。
- Opportunity 新增 Keyset/Cursor Pagination API；Observation 同时支持 Cursor Pagination。
- Docker Compose 新增一次性 `migrate` 服务，API / Worker 不再竞争执行 Alembic。
- 新增 WorkerHeartbeat，记录 worker mode、状态、最后心跳、最后成功与迭代数。
- 新增 Retention Policy：CollectionRun / AuditLog / AlertEvent 可清理；RawObservation 作为主证据默认永久保护，未完成冷归档前禁止破坏性删除。
- 新增 `maintenance` Worker 模式，执行 Full Reconciliation + Retention。

### 当前完整产品能力

- Source Connector Contract：官方 API、官方 Feed/Export、公开网页、人工导入、授权 App Observation。
- GitHub REST Search、Google Trends Trending Now RSS、可配置 RSS / Atom Feed。
- Raw Observation、关键词发现、7/30/90 日趋势、关系图、Watch Keywords。
- Persistent Probe、CollectionRun、Source Circuit Breaker、Analysis Queue。
- Opportunity Cluster、结构化分析、研究工作流、Alert Inbox、Source Preference。
- Observation / Opportunity 检索与导出、Audit Log、生产 Docker / Backup / Restore。

## 本地启动

```bash
./scripts/run_product.sh
```

Worker：

```bash
./scripts/run_worker.sh --mode all --interval 60
```

打开 `http://127.0.0.1:8000/`。

## 生产部署

生产模式强制：

- PostgreSQL
- `AUTH_MODE=rbac`
- `ALLOW_LEGACY_API_KEY=false`
- 独立 `migrate` Job 先完成数据库迁移，再启动 API/Worker

复制环境变量模板：

```bash
cp .env.example .env
```

至少填写 `POSTGRES_PASSWORD`，然后：

```bash
docker compose up -d --build
```

生产基线 `docker-compose.yml` 只启动 PostgreSQL、迁移、API 和真实 Worker；它不包含 Mock Mail、Webhook、Analysis 或 Enterprise Messaging，也不依赖这些服务的健康状态。生产通知默认使用 `EMAIL_DELIVERY_PROVIDER=smtp`，但 `EMAIL_DELIVERY_ENABLED=false`；启用通知前必须提供真实 SMTP 配置。

本地联调若需要 Mock 服务，必须显式叠加开发文件：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

开发覆盖层中的 Mock 只绑定到宿主机回环地址，不能成为生产部署的隐式依赖。

首次部署后创建第一个 OWNER：

```bash
docker compose run --rm api python -m app.admin_cli create-user owner --role OWNER
```

默认 Compose 包含 PostgreSQL、Migration、API、Collection/Analysis/Alert Worker，以及周期运行的 Maintenance Worker。`maintenance` profile 仍保留一次性手工维护入口。

## 鉴权与权限

```text
APP_ENV=development|production|test
AUTH_MODE=disabled|write|all|rbac
ALLOW_LEGACY_API_KEY=false
```

完整产品生产环境使用 `rbac`。角色：

- `OWNER`：系统所有者，可管理 OWNER/ADMIN 等用户。
- `ADMIN`：管理普通用户和系统配置，但不能创建/修改 OWNER。
- `RESEARCHER`：研究、关注词与业务写操作。
- `VIEWER`：只读。

Web 使用 HttpOnly Session Cookie；修改请求需要 CSRF Token。浏览器不保存主 API Key。自动化客户端可由用户签发 Personal API Token，Token 的有效权限始终受当前用户角色上限约束。

## 数据备份与恢复

SQLite：使用 SQLite Online Backup API，并执行 `PRAGMA integrity_check`。

PostgreSQL：使用系统 `pg_dump / pg_restore`。备份密码通过 `PGPASSWORD` 传递，不写入 CLI argv。

```bash
python scripts/backup_database.py --output-dir backups
python scripts/restore_database.py backups/<file> --confirm-restore
```

PostgreSQL CLI 默认恢复到新的 staging database，并验证 Alembic Revision 与关键表；不会直接覆盖生产库。确认 staging 验证通过后，可显式使用 `--promote-staging` 切换。`--unsafe-in-place` 仅保留为明确的兼容/应急路径。

原始 Observation 主记录保持为研究证据。较大的 `raw_payload` 可使用 maintenance 或归档 CLI 转存为 gzip JSONL，并记录 SHA-256；恢复时会验证路径与文件 Hash。

## 主要 API

- `/api/v1/watch-keywords`
- `/api/v1/opportunities`
- `/api/v1/opportunities/{id}/research`
- `/api/v1/alerts/rules`
- `/api/v1/alerts/events`
- `/api/v1/sources`
- `/api/v1/sources/{id}/preference`
- `/api/v1/observations`
- `/api/v1/probes/tasks`
- `/api/v1/collection-runs`
- `/api/v1/audit`
- `/api/v1/dashboard`
- `/api/v1/exports/opportunities.csv`
- `/api/v1/exports/observations.csv`

完整 API 可查看 FastAPI `/docs`。

## 完整验收

```bash
./scripts/validate_product.sh
```

固定验收包含：

- 全部 pytest
- Python compileall
- Shell syntax
- TypeScript 前端构建 + 编译产物 `node --check` + 无 localStorage 凭据检查
- Docker Compose YAML 结构
- Alembic upgrade/check/downgrade
- PostgreSQL offline DDL
- 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.7.1 → 0.8 数据迁移验证
- SQLite 真实 backup → mutate → restore E2E
- Fresh DB + 真实 Uvicorn RBAC/CSRF HTTP E2E
- Dependency lock + SBOM dependency fingerprint

## 当前未宣称完成的范围

完整产品开发仍在继续。当前没有虚构以下能力已经完成：

- 闲鱼真实公开商品 Connector
- 百度指数正式 Connector
- 招聘平台 Connector
- 抖音指数 / 微信指数
- Google Trends Alpha API Provider
- Android 模拟器真实 Instrumentation Runtime
- 真实 PostgreSQL Server E2E（当前环境无 PostgreSQL Server）
- 生产 LLM / n8n 凭据联调
- 外部通知渠道（当前预警为系统内 Inbox）

- 真实 PostgreSQL 多 Worker 并发/恢复 E2E（当前环境无 PostgreSQL Server / Docker Runtime）
- 托管 PostgreSQL `pg_trgm` Extension 权限实机验证
- 完整 OpenTelemetry 分布式 Trace（当前已有结构化日志、Trace ID 与 Metrics）
- RawObservation PostgreSQL 时间分区（当前已完成 raw payload 冷归档）
- React 前端迁移（当前为正式 TypeScript 模块化前端；环境无法联网安装新 npm 依赖）
- Playwright 浏览器 E2E 实际运行（脚本已实现，但当前 Chromium 被系统 `URLBlocklist=["*"]` 策略阻断导航）

这些是后续完整产品阶段任务，不再作为“可选 MVP 增强”。

## 0.7.1 Review Correctness Fixes

0.7.1 is a correctness/security review release. It fixes cluster truncation, bounded-reconciliation dormancy corruption, alert-queue concurrency/retry behavior, PostgreSQL derived-analysis serialization, deterministic graph selection, immediate watch-keyword lifecycle recalculation, production read-authentication, and PostgreSQL CLI backup URL handling.
