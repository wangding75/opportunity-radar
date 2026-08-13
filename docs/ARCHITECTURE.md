# Architecture

## Core boundary

数据获取和机会解释严格隔离：

`SourceConnector -> RawObservation -> NormalizedItem -> KeywordMention -> Trend/Graph -> Opportunity -> ProbeTask -> CollectionRun`

### Acquisition methods

- OFFICIAL_API
- OFFICIAL_EXPORT
- PUBLIC_WEB
- MANUAL_IMPORT
- INSTRUMENTED_APP

Evidence Quality 与 Acquisition Risk 是两个独立维度，不能混用。商业模式 Risk Score 也独立于采集风险。

## Observation semantics

RawObservation 是可追溯原始证据层。

- 相同来源、查询、内容、payload 指标和关键 App 版本在**同一天**重复提交视为幂等重试。
- 跨日再次观察，或同日 payload 指标/App 版本发生变化时保留新快照，用于时间序列、供给持续性和 Schema Drift 分析。
- 外部带时区时间戳进入数据库前统一转换为 timezone-naive UTC。

## Derived analysis

### Keyword lifecycle

关键词状态依赖近期窗口，不以历史累计量永久保持 ACTIVE：

`DISCOVERED -> WATCHING -> ACTIVE -> TRENDING -> DECLINING -> ARCHIVED`

### Trend

KeywordTrendDaily 保存最近 90 日按天聚合的 Observation 数量和独立来源数量。当前输出 7/30/90 日窗口和 7/30 日增长率。

### Graph

KeywordRelation 记录同一 NormalizedItem 内关键词的共现关系。默认 API 只返回最近 90 日仍出现的关系，避免长期陈旧关系污染结果。

### Opportunity

Opportunity Engine 使用确定性规则，分别计算：

- Demand Score
- Supply Score
- Execution Score
- Cross-source Score
- Saturation Score
- Business Risk Score

Evidence Quality 会影响有效证据权重。超过近期窗口的旧机会会转为 DORMANT，而不是永久保持高分。

### Probe Planner

Probe Planner 只针对 WATCHING / ACTIVE / TRENDING 关键词扩展少量查询，并根据 Connector Capability 选择可查询数据源，防止关键词笛卡尔积爆炸。

## Instrumented App boundary

系统定义授权模拟器 / App 研究 Observation 的接入 Contract，但不实现认证绕过、验证码绕过、反机器人或设备风控规避、付费权限绕过、私人数据访问。

进入 RawObservation 前执行数据最小化：

- 递归删除 token、cookie、authorization、手机号/邮箱字段、精确地址/经纬度、IMEI/IMSI/device_id 等常见敏感键。
- title/text 中常见手机号和邮箱进行脱敏。
- URL 只保留 http/https，并删除敏感查询参数和 fragment。
- App payload 可按 app_version 生成 Schema Drift 报告，检测新增/删除字段。

普通 Import API 不允许声明 `OFFICIAL_API` 或 `EvidenceQuality.A`，避免人工数据伪装为官方一手证据。

## Schema management

应用运行时不调用 `Base.metadata.create_all()`。Schema 只能通过 Alembic 迁移进入运行数据库，避免 ORM 与生产 Schema 静默漂移。


## Source query modes

Connector discovery semantics are explicit:

- `KEYWORD`: accepts keyword probes generated from the keyword graph.
- `REGION`: accepts region/feed probes owned by the connector.
- `PUSH_ONLY`: cannot be actively collected; observations arrive through a dedicated ingress.
- `SCHEDULED`: connector-owned fixed feed/task; it does not accept keyword expansion.

Connector-owned scheduled queries allow region/feed sources to participate in the same persistent task runner without pretending that a region code is a keyword.

## Collection runtime

`ProbeTask` persists query, intent, priority, interval and retry state. `CollectionRun` persists every active collection attempt. A failed attempt is committed as FAILED and the task receives bounded exponential backoff. The worker is a separate process (`python -m app.worker`) so multiple Web workers do not each create hidden scheduler loops.

## Opportunity clustering and structured analysis

0.4 起 Opportunity 不再与 Keyword 1:1 绑定。近期候选关键词通过 `KeywordRelation` 强共现边形成有限连通分量，每个分量最多保留 8 个高分关键词，并选取最高信号关键词作为 PRIMARY。

`OpportunityKeyword` 保存 Cluster Membership；`OpportunityEvidence` 保存跨关键词去重后的真实证据。

Structured Analysis 与评分解耦：

- Score 仍由 deterministic rule engine 计算，不允许外部 LLM 直接修改评分。
- 默认 `heuristic` provider 生成稳定、可测试的 summary / target_user / business_model / monetization / risk_notes。
- `http` provider 使用项目自有 JSON Contract，可接 LLM Gateway / n8n / internal inference service，不绑定具体模型厂商。
- 新证据到达时先同步生成 heuristic 基线；如果启用外部 Provider，状态改为 `PENDING`。
- 外部 HTTP 调用由独立 analysis runtime 执行，不占用采集事务。Runtime 使用原子 claim 防并发重复分析，并支持 `ANALYZING` stale recovery 和有界指数退避。
- Provider 失败时保留 heuristic 内容，`analysis_status=DEGRADED`，技术错误写入 `analysis_error`，不会污染 `risk_notes`。
- 成功结果按 analysis signature 去重；signature 包含 evidence text hash / quality / URL 等关键证据语义。
- 对外发送的 evidence 数量和文本长度受限，HTTP 响应体和结构化字段也有大小约束。

## Source health and circuit breaker

每个主动 Connector 都可以持久化 `SourceHealthState`：

`UNKNOWN -> HEALTHY | DEGRADED -> CIRCUIT_OPEN`

- 单次失败：consecutive_failures +1，状态 DEGRADED。
- 连续 3 次失败：打开 30 分钟 Circuit。
- Circuit 打开时，不调用 Connector，CollectionRun 记录 SKIPPED。
- 任意成功采集会清零连续失败并恢复 HEALTHY。
- 明确的上游限流可直接按 Retry-After / reset 时间打开 Circuit，不需要先累计三次失败。
- SourceHealthState 同时持久化运行总数、成功/失败/限流次数、成功率所需计数、最近/平均耗时和最近抓取/写入量。

这一层与 ProbeTask 的指数退避独立：Probe 退避控制单任务频率，Circuit Breaker 保护整个数据源。

## Readiness invariant

`/ready` 不只检查表名，还要求数据库 `alembic_version` 与应用要求的 revision 完全一致。Schema 落后一版即返回 503 migration_required，避免“旧库 + 新代码”被误认为可服务。

## Product workflow layer (0.6+)

分析结果与人工研究状态解耦。`OpportunityResearch` 保存用户工作流状态、收藏、优先级、标签与备注，因此 Opportunity 因新证据重新计算时不会覆盖人工研究记录。

`SeedKeyword` 保存主动关注主题，并给对应 Keyword 提供 WATCHING/score floor，使“尚无数据的已知关注方向”也能进入 Probe Planner。

`AlertRule -> AlertEvent` 提供内部事件 Inbox。Alert event key 包含 Opportunity analysis signature；同一证据版本幂等，新证据版本可在 cooldown 允许时产生新事件。

`SourcePreference` 是 Connector descriptor 之外的运行时控制层。Descriptor 表示代码能力，Preference 表示当前用户是否允许调度/主动采集，两者不能混用。

`AuditLog` 由 HTTP middleware 记录写操作元信息。审计不保存请求正文、Authorization/API Key 或 Observation payload。

## Production boundary

`APP_ENV=production` 强制 PostgreSQL 和 API Key 鉴权。SQLite 启用 foreign keys、busy timeout 和 WAL，仅作为本地单用户开发/研究数据库。

## 0.7 Scale & Correctness architecture

### Incremental derived analysis

Ingestion passes the newly materialized `NormalizedItem` IDs into the derived-analysis pipeline. The pipeline resolves only the changed `KeywordMention` rows, refreshes metrics for those keywords, rebuilds only the affected daily trend buckets, and recomputes Opportunity clusters only within the strong-relation closure around the changed keywords.

A separate `maintenance` worker mode performs full reconciliation. This split keeps normal ingestion bounded while retaining a deterministic recovery path for relation expiry, stale lifecycle transitions, and drift correction.

### Stable Opportunity identity

`opportunity_key` is stable from 0.7 onward. Cluster membership is mutable state recorded separately through `cluster_signature`, `cluster_generation`, `OpportunityClusterVersion`, and `OpportunityLineage`. Merge/split decisions use keyword overlap and preserve existing research-bearing opportunities when possible.

### Event-driven alerts

Opportunity changes enqueue `AlertEvaluationQueue` rows. The alerts worker evaluates only queued opportunities against enabled rules. Manual full evaluation remains available for administrative reconciliation.

### PostgreSQL search

Migration 0007 enables `pg_trgm` on PostgreSQL and adds GIN trigram indexes for Opportunity and RawObservation text search. API search semantics remain portable `ILIKE`; PostgreSQL can use the indexes without creating a separate Elasticsearch dependency.
