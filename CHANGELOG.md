## 0.8.1-global-review

- Global correctness/security review with direct fixes rather than audit-only findings.
- Preserve stable Opportunity identity on splits/merges; prevent duplicate pending lineage rows with autoflush disabled.
- Backtest now counts mature threshold crossings using exact pre-window state instead of treating missing future history as failure.
- Fix Probe lease/stale timing, task progress heartbeats, recurring production maintenance and maintenance progress heartbeats.
- Serialize manual/worker alert evaluation on PostgreSQL and harden alert revision/backoff behavior.
- Restrict evidence ingestion/import to ADMIN; restrict operational task/run endpoints and redact source internal errors for non-admin readers.
- Enforce true JSON payloads, request-body limits, streaming external response limits, unsafe XML declaration rejection and production HTTPS for external analysis.
- Bound Opportunity evidence queries to the active 90-day window while preserving historical first-seen dates.
- Fix PostgreSQL Compose password URL handling, staged restore database naming and archive verification.
- Extend Instrumented App sanitizer for URL userinfo, camelCase credential keys and API keys.
- Wire cursor pagination and password reset into the product UI; ADMIN no longer sees misleading OWNER edit controls.
- Validate recurring maintenance and password-safe PostgreSQL Compose configuration in product validation.

## 0.8.0-product-hardening

- Added multi-user RBAC: OWNER / ADMIN / RESEARCHER / VIEWER, HttpOnly session cookies, CSRF, personal API tokens, login lockout and auth-record cleanup.
- Removed browser `localStorage` API-key authentication; production now requires RBAC and disables the legacy shared key.
- Added user-management APIs/UI and role-safe token authorization; demotion immediately limits previously issued token scopes.
- Added TypeScript frontend modules and deterministic frontend build validation.
- Added scoring model version, persisted score snapshots, replay and baseline backtest APIs.
- Added raw-payload cold archive/restore with gzip JSONL, SHA-256, path protection and retained primary evidence rows.
- PostgreSQL restore now defaults to staged restore + validation; promotion is explicit and the prior production database is retained for rollback.
- Added structured JSON logging, trace/request correlation IDs, authenticated metrics and database queue/worker/source-health gauges.
- Split API routers into auth/research/operations/scoring modules.
- Added exact Python production/development locks, TypeScript lock and CycloneDX SBOM dependency-fingerprint validation.
- Added fresh-DB real Uvicorn RBAC/CSRF HTTP E2E and 0.7.1 -> 0.8 migration validation.
- Fixed 0009 ORM/Alembic uniqueness drift discovered by full `alembic check`.

## 0.7.0-scale-correctness

- 派生分析改为受影响 Keyword / Day / Opportunity Component 增量刷新，保留 maintenance 全量纠偏。
- Keyword Graph 改为批量关系读写；新增 KeywordRelationSource，消除 pair-level 历史 source recount。
- Opportunity Identity 稳定化；新增 Cluster Version 和 Merge/Split Lineage。
- 聚类合并/拆分不再依赖 `cluster:min(keyword_id)` 重建身份，人工 Research 状态持续保留。
- Alert Rule 增加持久变化队列，Worker 默认只评估发生变化的 Opportunity。
- 新增 Opportunity Cursor Pagination，Observation 支持 Cursor Pagination。
- PostgreSQL 增加 pg_trgm + GIN 搜索索引。
- Docker 部署增加独立 migrate service，API/Worker 不再同时跑 Alembic。
- 新增 WorkerHeartbeat 与 maintenance Worker 模式。
- 新增 Retention Policy；原始 Observation 作为研究主证据保持保护状态。
- 新增 0.6 -> 0.7 数据升级验证与规模正确性专项回归。

# Changelog

## 0.5.0 - Analysis Runtime & Source Observability

- 外部 Structured Analysis 从采集事务中拆离，新增 PENDING / ANALYZING / DEGRADED / READY 持久状态执行链。
- 新增外部分析原子 claim、10 分钟 stale recovery、失败指数退避与独立 `/analysis/run-pending` 执行入口。
- Worker 在 Probe 执行后继续处理到期外部分析，不再由 ingestion 请求同步等待模型响应。
- 外部分析 evidence 条数、文本长度和 HTTP 响应体均设上限，降低超大请求和异常响应风险。
- Opportunity Detail 新增 Evidence Summary，并限制 evidence 返回数量/文本长度；显示 Evidence Quality 与 Acquisition Method。
- Analysis Signature 纳入 evidence text hash、quality、item_type 和 URL，避免证据变化但标题未变时错误复用旧分析。
- SourceHealthState 新增总运行数、成功/失败/限流次数、成功率、最近/平均耗时及最近抓取/写入量。
- CollectionRun 新增 duration_ms。
- Connector 新增上游 Rate Limit 语义；GitHub / Google Trends 遇到 429 或确定配额耗尽时立即按 Retry-After/Reset 打开 Circuit。
- 新增可配置 HTTPS RSS/Atom Feed Connector，支持官方 Feed（B 级）和普通公开 Feed（D 级）。
- `/ready` 改为精确校验 Alembic revision，防止代码升级但数据库未迁移仍错误报告 READY。
- 新增 Alembic `0005_analysis_queue_observability` 和 `0.4 -> 0.5` 数据库升级兼容验收。
- 回归测试扩充至 43 项。

## 0.4.0 - Opportunity Intelligence

- Opportunity 从单 Keyword 提升为基于近期 KeywordRelation 的多关键词 Cluster。
- 新增 `OpportunityKeyword`，保存 PRIMARY / RELATED 关键词及权重。
- Opportunity 新增 summary、target_user、business_model、monetization、risk_notes 等结构化分析字段。
- 新增 deterministic heuristic Analysis Provider，保证无外部模型时仍有可测试结果。
- 新增 vendor-neutral HTTP Structured Analysis Provider Contract，可对接 LLM Gateway、n8n 或内部推理服务。
- 外部 Analysis Provider 失败自动 fallback，技术错误与 Business Risk 分离；失败结果不缓存并允许后续重试。
- 新增 SourceHealthState 和连续失败 Circuit Breaker；3 次连续失败后熔断 30 分钟。
- 熔断期间 CollectionRun 记录 SKIPPED，不继续请求故障源。
- 来源成功恢复后自动清除 failure/circuit 状态。
- Dashboard 增加 Open Source Circuits，Opportunity 展示摘要与聚类关键词数。
- 默认 Opportunity API 隐藏 DORMANT，仍可通过 `include_dormant=true` 查询历史。
- 新增 Alembic `0004_clusters_analysis_health`。
- 新增 0.3 -> 0.4 数据库升级兼容验收。
- 回归测试扩充至 30 项。

## 0.3.0 - Data Runtime

- 新增 Source QueryMode：KEYWORD / REGION / PUSH_ONLY。
- Instrumented App Connector 改为真实 PUSH_ONLY 语义；主动采集明确拒绝，移除虚假空结果实现。
- 新增 Google Trends Trending Now RSS 官方导出 Connector。
- Google Trends Feed 与关键词 Probe 隔离；默认按 US/TW 地区周期发现，可通过 `GOOGLE_TRENDS_GEOS` 调整。
- 新增 `ProbeTask` 持久任务表：优先级、周期、next_run_at、失败次数、错误信息。
- 新增 `CollectionRun` 采集运行历史，失败也持久化。
- 新增 Probe Plan -> Task Sync -> Run Due 完整执行链。
- Probe 失败增加有界指数退避；成功后恢复按热度周期执行。
- 新增独立 `app.worker` 与 `scripts/run_worker.sh`，避免把后台循环绑死在 Web 进程。
- `/collect/{source_id}` 接入统一 CollectionRun 执行器。
- Dashboard 增加 Active Probes 和 24h Failed Runs 指标。
- 新增 Alembic `0003_probe_scheduler_and_runs`。
- 新增 Google Trends RSS、Probe Scheduler、Push-only 契约测试。

## 0.2.0 - Signal Engine

- 新增 KeywordRelation 共现图谱和 7/30/90 日趋势。
- 新增 Opportunity / OpportunityEvidence 和确定性机会评分。
- 新增 Probe Planner。
- 修复跨天快照、时区、payload 指标变化去重和关键词截断等问题。
- 增加 App Observation Sanitizer、Schema Drift、Provenance 校验和 `/ready`。
- 应用 Schema 统一改由 Alembic 管理。

## 0.1.0 - MVP Baseline

- 建立工程、Source Contract、RawObservation、Normalizer、Keyword、GitHub Connector、Import API、Instrumented App 入库契约和 Dashboard 基线。

## 0.6.0-product-core

- 正式从 MVP 开发口径切换到完整产品开发口径。
- 新增 Opportunity Research 工作流：收藏、状态、优先级、标签、备注。
- 新增 Watch Keywords 主动关注词及 Probe 接入。
- 新增 Alert Rule / Alert Event 内部预警 Inbox。
- 新增 SourcePreference 运行时启停。
- 新增 Observation 检索、Opportunity/Observation CSV 导出。
- 新增 API Key 鉴权、Request ID、安全响应头、写操作 Audit Log。
- 新增七工作区 Web UI。
- Worker 支持 collection / analysis / alerts 独立模式。
- 新增生产 Docker Compose：PostgreSQL + API + Worker。
- 生产模式强制 PostgreSQL、鉴权和长 API Key。
- 新增 SQLite 在线备份/恢复 E2E，PostgreSQL pg_dump/pg_restore 支持。
- SQLite 开启 foreign_keys / WAL / busy_timeout。
- 新增 0006_product_workflow_alerts 迁移和 0.5 -> 0.6 数据升级验证。
- CSV 导出增加 spreadsheet formula injection 中和。

## 0.7.1-review-fixes

- Fixed opportunity clusters silently dropping members beyond the analysis payload limit.
- Prevented bounded reconciliation from dormancy-resetting opportunities outside its processed slice.
- Preserved active parent identities across split+merge cluster changes and added explicit lineage.
- Added revisioned, leased, retryable AlertEvaluationQueue processing for multi-worker safety.
- Added PostgreSQL transaction-scoped derived-analysis locking and source-health row locking.
- Made keyword graph fan-out deterministic and query-keyword aware.
- Recalculated watch keyword lifecycle immediately after enable/priority changes.
- Production now requires full API authentication (`AUTH_MODE=all`); authenticated CSV exports use fetch.
- Fixed PostgreSQL pg_dump/pg_restore SQLAlchemy URL compatibility and removed DB passwords from argv.
- Made PostgreSQL backup writes atomic and added archive preflight before destructive restore.
- New/updated alert rules now evaluate already-active opportunities instead of waiting for a future signal.
- Fresh alert revisions reset stale failure/backoff history; poison queue rows no longer block unrelated alerts.
- Fixed injected HTTP-client ownership, best-effort connector shutdown, response-size limits, and persistent worker client reuse.
- Split production workers by collection/analysis/alerts and keep heartbeat writes isolated from business transactions.
- Source-health updates are race-safe on PostgreSQL; audit sink failures are logged instead of silently discarded.
- Oversized strong-relation closures now fail closed to full reconciliation instead of returning partial clusters.
