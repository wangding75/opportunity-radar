# React 原型 ↔ 后端能力差异与开发计划

日期：2026-09-04  
UI 基准：根目录 React 原型的 34 个页面与 27 个状态  
后端基准：当前 `backend/app` FastAPI、SQLAlchemy 模型和已通过的 379 个测试

跨前端、后端、页面迁移和发布的完整任务顺序见 [`REACT_OPTIMIZATION_EXECUTION_PLAN.md`](REACT_OPTIMIZATION_EXECUTION_PLAN.md)。

## 1. 目标与约束

本文把 React 原型表达的产品能力转成后端可执行开发契约。它不是要求后端机械实现每一个视觉按钮；纯导航、局部筛选和展示开关保持 UI-only，涉及持久化、权限、审计、异步任务或跨用户共享的动作必须有真实服务端契约。

状态定义：

- `PRESENT`：现有接口和语义可直接使用。
- `PARTIAL`：有相近数据或接口，但字段、对象、状态机或写能力不完整。
- `MISSING`：现有后端没有等价能力。
- `UI_ONLY`：无需后端。

约束：

1. 禁止用前端 state 或 toast 伪造保存、发布、发送、重试、授权等成功结果。
2. 自动推导的 Opportunity stage 不等价于用户可编辑生命周期状态。
3. 管理员批量 worker 命令不等价于用户级“立即运行/重试某任务”。
4. `OpportunityResearch` 单行研究备注不等价于研究工作流、步骤、结果和发布状态。
5. Webhook endpoint 不等价于 Slack、Teams、邮件、SSO 等通用集成目录。
6. 所有新写接口必须执行服务端 RBAC、审计、幂等和并发保护。

## 2. 已有可复用接口

| 能力 | 现有接口 | 权限 |
|---|---|---|
| 登录/登出/当前用户 | `POST /api/v1/auth/login`、`POST /api/v1/auth/logout`、`GET /api/v1/auth/me` | public/write/read |
| Personal API Token | `GET/POST/DELETE /api/v1/auth/tokens...` | read/write |
| 用户管理 | `GET/POST/PATCH /api/v1/admin/users...` | admin |
| 工作台 | `GET /api/v1/dashboard` | read |
| 情报/Observation 列表 | `GET /api/v1/observations` | read |
| 关键词/趋势/关系图 | `GET /api/v1/keywords`、`GET /keywords/{id}/trend`、`GET /keyword-graph` | read |
| 关注关键词 | `GET/POST/PATCH /api/v1/watch-keywords...` | read/write |
| 机会 | `GET /api/v1/opportunities/page`、`GET /opportunities/{id}` | read |
| 机会研究备注 | `PATCH /api/v1/opportunities/{id}/research` | write |
| 评分历史 | `GET /api/v1/scoring/opportunities/{id}/history` | read |
| 来源/健康/偏好 | `GET /sources`、`GET /sources/health`、`PATCH /sources/{id}/preference` | read/write |
| Probe 与运行摘要 | `GET /probes/plan`、`GET /probes/tasks`、`GET /collection-runs` | read |
| 告警规则 | `GET/POST/PATCH /alerts/rules...` | read/write |
| 告警事件 | `GET /alerts/events`、`PATCH /alerts/events/{id}` | read/write |
| Webhook endpoints | `GET/POST/PATCH/DELETE /webhook-endpoints...` | read/admin |
| 审计/worker | `GET /audit`、`GET /workers` | admin |
| 健康度 | `GET /health`、`GET /ready`、`GET /metrics` | public/public/read |
| 导出 | opportunity、observation、weekly trend CSV | read |

## 3. 34 页面能力矩阵

| 页面 | 原型关键能力 | 当前状态 | 现有契约/缺口 | 后端任务 |
|---|---|---|---|---|
| P01 今日雷达 | 6 KPI、机会/信号/告警/趋势/研究/系统状态 | PARTIAL | `/dashboard` 可复用；研究进展、来源异常、跨模块统一时间窗不足 | BE-01、BE-03、BE-08 |
| P02 情报列表 | 搜索、筛选、收藏、订阅、预览、新建观察 | PARTIAL | `/observations` 有列表；无收藏、订阅、保存视图、手工创建 | BE-01 |
| P03 情报详情 | 详情、实体/关系、原文、收藏、关键词、转机会、监控、摘要/翻译/导出/忽略 | MISSING/PARTIAL | 没有 detail endpoint 和用户处理状态；现有列表字段只能支持只读摘要 | BE-01、BE-02、BE-04、BE-08 |
| P04 关键词发现 | 候选、趋势、评估、关注、忽略、合并、建监控 | PARTIAL | keywords/watch 可用；无 dismissal/merge/人工评估 | BE-01 |
| P05 关注关键词 | 新增、暂停/启用、优先级、趋势/图谱 | PRESENT/PARTIAL | watch GET/POST/PATCH 可用；缺删除与用户级展示偏好 | BE-01 |
| P06 趋势分析 | 多关键词对比、异常、导出、关联机会 | PARTIAL | 现有单关键词 trend/weekly report；缺 compare 查询与图表导出任务 | BE-01、BE-08 |
| P07 关系图谱 | 多类实体图、快照、实体聚焦、关联机会 | PARTIAL | `/keyword-graph` 仅关键词关系；没有实体/机会统一图 | BE-01、BE-02 |
| P08 机会池 | 分页筛选、关注、公共 ID、导出 | PARTIAL | opportunity page/CSV 可用；缺用户关注和原型字段 | BE-02 |
| P09 机会详情 | 状态、负责人、证据、分析、研究、备注、下一步 | PARTIAL | detail 很丰富；research patch 只覆盖 starred/priority/notes/tags/status，且 status 不是完整生命周期 | BE-02、BE-03 |
| P10 结构化分析 | 维度评分、编辑、版本、导出 | PARTIAL | opportunity analysis/score breakdown 可读；缺用户编辑、版本发布和导出报告 | BE-02、BE-08 |
| P11 研究工作流列表 | 新建、筛选、进度、负责人 | MISSING | 无 ResearchWorkflow 实体/API | BE-03 |
| P12 研究工作流详情 | 步骤、暂停/恢复/取消、重试、任务清单、活动 | MISSING | `OpportunityResearch` 不等价 | BE-03 |
| P13 研究结论 | KPI、证据分布、结果列表、发布、通知、导出 | MISSING | 无 ResearchResult/发布契约 | BE-03、BE-08 |
| P14 来源管理 | 来源目录、连接、编辑、启停、批量/全量同步 | PARTIAL | registry/health/preference 只支持有限读取和启停偏好 | BE-05 |
| P15 来源详情 | 配置、同步、统计、产出、关联计划 | PARTIAL | 可组合 source health/observations/runs；无统一详情、配置和 run-now | BE-05、BE-04 |
| P16 来源健康 | 聚合分数、时间序列、异常历史、刷新 | PARTIAL | 当前 health 是状态快照；缺历史指标和按来源错误事件 | BE-05、BE-08 |
| P17 监控计划 | CRUD、模板、暂停/启用、手动运行 | MISSING/PARTIAL | probe plan/task 可读；无稳定 PLAN 资源与用户状态机 | BE-04 |
| P18 监控计划详情 | 配置、来源、统计、最近运行、编辑、run-now | MISSING/PARTIAL | 只能从 probe/task/run 拼装，语义不等价 | BE-04 |
| P19 运行记录 | 查询、状态、分页、导出、日志、复跑 | PARTIAL | `/collection-runs` 只有摘要读取 | BE-04、BE-08 |
| P20 运行详情 | 阶段、日志、产出、错误、关联对象、重试 | MISSING/PARTIAL | 无单 run detail/log/output/retry API | BE-04 |
| P21 分析队列 | 队列、worker 负载、优先级、失败筛选、单项控制 | MISSING/PARTIAL | 可由 opportunity analysis_status 派生；admin run-pending 不等价 | BE-04 |
| P22 告警中心 | 列表、状态、批量处理、导出、关联对象 | PRESENT/PARTIAL | event GET/PATCH 支持 NEW/ACKNOWLEDGED/DISMISSED/RESOLVED；缺 batch/export/独立已读 | BE-06、BE-08 |
| P23 告警规则 | 列表、新建/编辑/启停、模板、测试、删除、导出 | PARTIAL | GET/POST/PATCH 可用；缺 test/delete/template/export | BE-06、BE-08 |
| P24 工作区设置 | 基本信息、logo、领域、存储、导出/清理/重置/删除 | MISSING | 无 Workspace 资源；现有部署 settings 不可直接作为用户配置 | BE-07 |
| P25 成员管理 | 用户、邀请、重发、权限、导出 | PARTIAL | admin users 支持直接创建/修改；无邀请生命周期/邮件/导出 | BE-07、BE-08 |
| P26 角色与权限 | 角色矩阵、编辑、复制模板 | PARTIAL | 后端有固定角色和 scope 校验；无角色矩阵 API/自定义角色 | BE-07 |
| P27 账户安全 | 资料、密码/邮箱/手机、MFA、Passkey、恢复码、Token、会话、删号 | PARTIAL | auth/me 和 token 可用；其余基本缺失 | BE-07 |
| P28 外部集成 | 目录、OAuth、连通性、Slack/Teams/LLM/n8n 等 | MISSING/PARTIAL | webhook endpoint 可用；无通用 Integration/OAuth/secret reference | BE-07 |
| P29 审计日志 | 搜索筛选、详情、导出 | PARTIAL | `/audit` 仅 action + limit；缺完整过滤、游标、detail/export | BE-08 |
| P30 系统诊断 | 服务清单、健康历史、全量检测、报告 | PARTIAL | health/ready/metrics/workers 可用；缺统一诊断快照和受控 probe | BE-08 |
| P31 全局搜索 | 跨对象检索、分类、保存搜索 | PARTIAL | 可前端并行多个列表 API；无统一排序/游标/权限裁剪搜索 | BE-08 |
| P32 登录 | 密码、MFA、SSO、找回密码 | PARTIAL | 密码登录已存在；MFA/SSO/reset 缺失 | BE-07 |
| P33 无权限 | 解释、返回、申请权限 | MISSING/UI_ONLY | 403 展示 UI-only；访问申请需持久化/通知 | BE-07 |
| P34 404 | 搜索、推荐入口、帮助 | UI_ONLY/PARTIAL | 404 UI-only；搜索使用 BE-08；不要伪造人工客服 | BE-08 |

## 4. 后端开发包

### BE-00：React 发布、公共 ID 与会话启动契约（P0）

**状态：部分完成（2026-09-04）**。React 多阶段发布、deep link、`UI_MODE` 回滚开关已落地；`GET /api/v1/auth/bootstrap`、统一错误信封和 Opportunity 的稳定 `public_id` 已可用。错误响应在迁移期保留 FastAPI `detail`；Observation、Research、Plan、Run、Alert 的 public ID 与跨实体 URL 仍未开发，不能把当前 Opportunity 覆盖范围误认为全域完成。

目标：让 React 成为真正的生产入口，并建立所有业务接口共用的基础契约。

需要完成：

1. Docker 多阶段构建 React，将产物发布到明确的静态目录；旧 UI 退出默认入口。
2. 为所有非 `/api`、`/static`、`/health`、`/ready`、`/metrics` 路径返回 React `index.html`，确保 deep link 刷新可用。
3. Google Fonts 改自托管或移除；CSP、缓存策略、asset hash 与 source map 策略同步更新。
4. 统一公共 ID。Opportunity 已将现有不可变、UUID-backed `opportunity_key` 以 `public_id` 输出并接受为详情 URL；兼容期保留整数读取。Observation、Research、Plan、Run、Alert 仍需提供不可变 `public_id`，新产品链接不得继续输出数据库整数 ID。
5. 建议新增 `GET /api/v1/bootstrap`，一次返回 `current_user`、`role/scopes`、feature flags、workspace 摘要、服务端时间和可用模块；未登录返回 401，不返回伪用户。
6. 统一错误 envelope：`code`、`message`、`field_errors`、`request_id`、`retryable`；429 保留 `Retry-After`。

验收：任一 React 路由直接访问/刷新成功；未登录与无权限行为可预测；静态资源 CSP 无报错；前端 URL 不依赖数据库自增 ID。

### BE-01：情报、关键词、趋势与关系（P0/P1）

**状态：部分完成（2026-09-08）**。既有 `GET /api/v1/observations` 已升级为输出内容寻址的 `obs_…` `public_id`，保留原 cursor/offset 分页和整数 ID 兼容；`GET /api/v1/observations/{public_id}` 已提供不含原始 payload 的详情读取。**用户级 Observation state 已落地（2026-09-08）**：新增 `UserObservationState` 模型与迁移 `0032_user_observation_states`（user_id、observation_id、bookmarked、dismissed_at、notes、updated_at，唯一约束 `(user_id, observation_id)`），接口 `GET/PUT/DELETE /api/v1/observations/{public_id}/state`；VIEWER 也可维护自己的收藏/忽略/备注，写操作经 CSRF（会话）、审计日志与统一错误 envelope，PUT 幂等；`/observations` 列表与详情返回当前用户的 `user_state`，未登录或开发匿名模式显式返回 `null`，不伪造收藏状态。订阅/保存搜索、人工创建以及关键词 merge 审计仍未实现。

新增/扩展模型：

- `UserObservationState(user_id, observation_id, bookmarked, dismissed_at, notes, updated_at)`。
- `SavedSearch` / `Subscription`，明确 query、对象类型、频率和 owner。
- 如需人工 Observation，记录 `origin=MANUAL`、创建者、原始附件/引用和证据等级，不能混同外部采集证据。
- Keyword dismissal/merge audit record；merge 必须保留 alias 与 lineage。

建议接口：

```text
GET    /api/v1/observations/{public_id}              # 已实现
GET    /api/v1/observations/{public_id}/state        # 已实现（2026-09-08）
PUT    /api/v1/observations/{public_id}/state        # 已实现（2026-09-08，幂等，VIEWER 可用）
DELETE /api/v1/observations/{public_id}/state        # 已实现（2026-09-08，幂等）
POST   /api/v1/observations                       # 人工创建，若产品确认需要
POST   /api/v1/subscriptions
GET    /api/v1/subscriptions
PATCH  /api/v1/subscriptions/{id}
DELETE /api/v1/subscriptions/{id}
POST   /api/v1/keywords/{id}/dismiss
POST   /api/v1/keywords/merge                     # admin，带 dry-run
GET    /api/v1/trends/compare?keyword_ids=...&since_days=...
GET    /api/v1/entity-graph?root_type=...&root_id=...
```

情报详情 response 至少包含来源、标题、正文/摘要、observed_at、source_url、acquisition_method、evidence_quality、content hash/证据 ID、实体、关键词、关联机会、关联运行和当前用户状态。不存在的关系返回空数组并带 capability，不允许前端猜测。

验收：P02–P07 不再引用 mock；收藏/忽略刷新后仍保持；merge 可审计且可追溯；图表所有点能回溯证据。

### BE-02：机会人工工作流与结构化分析（P0/P1）

现有 Opportunity 主要由分析流水线自动聚类和推导。原型需要一层用户工作流，不能直接覆盖自动字段。

新增/扩展：

- `workflow_stage` 与自动 `stage` 分离，或明确唯一权威状态机。
- owner/assignee、watchers、manual_priority、user_notes、version。
- `OpportunityEvidenceLink` 的人工增删来源、操作者和原因；保留算法生成 link 的只读 provenance。
- `StructuredAnalysisRevision`，保存输入、维度评分、生成器版本、引用、draft/published 状态。

建议接口：

```text
POST   /api/v1/opportunities
GET    /api/v1/opportunities/{public_id}
PATCH  /api/v1/opportunities/{public_id}          # If-Match/version
PUT    /api/v1/opportunities/{public_id}/watchers/me
DELETE /api/v1/opportunities/{public_id}/watchers/me
POST   /api/v1/opportunities/{public_id}/evidence
DELETE /api/v1/opportunities/{public_id}/evidence/{evidence_id}
GET    /api/v1/opportunities/{public_id}/activity
POST   /api/v1/opportunities/{public_id}/analysis-runs
GET    /api/v1/opportunities/{public_id}/analysis-revisions
PATCH  /api/v1/analysis-revisions/{id}
POST   /api/v1/analysis-revisions/{id}/publish
```

从情报“转为机会”使用 `POST /opportunities`，body 带 `seed_observation_ids` 与 `Idempotency-Key`；服务端执行去重并返回 created/existing，不允许前端固定跳到某个 OPP ID。

验收：P08–P10 的详情、状态、负责人、证据、备注、分析版本均服务端持久化；冲突返回 409；活动流包含 before/after 和 actor。

### BE-03：研究工作流、步骤与结论（P1）

这是当前最大业务域缺口。建议新增：

- `ResearchWorkflow(public_id, opportunity_id, name, depth, owner_id, status, progress, version, created_at...)`
- `ResearchStep(workflow_id, type, order, status, input, output, error, attempt_count...)`
- `ResearchTask(step_id, title, assignee_id, status, due_at...)`
- `ResearchResult(public_id, workflow_id, title, summary, payload, status, published_at, published_by...)`
- `ResearchEvidenceLink(result_id, evidence_id, claim_key, citation_order...)`
- `ResearchActivity(workflow_id, actor, action, detail, created_at)`

建议状态机：

```text
DRAFT -> QUEUED -> RUNNING -> PAUSED -> COMPLETED -> PUBLISHED
                    |            |
                    +-> FAILED <-+
RUNNING/PAUSED/FAILED -> CANCELLED
```

非法跳转返回 409；重试必须创建新 attempt，保留旧错误和输出。

建议接口：

```text
GET/POST /api/v1/research-workflows
GET/PATCH /api/v1/research-workflows/{public_id}
POST      /api/v1/research-workflows/{public_id}/actions/{pause|resume|cancel}
GET       /api/v1/research-workflows/{public_id}/steps
POST      /api/v1/research-steps/{id}/retry
GET       /api/v1/research-workflows/{public_id}/activity
GET/PATCH /api/v1/research-tasks/{id}
GET       /api/v1/research-results
GET       /api/v1/research-results/{public_id}
POST      /api/v1/research-results/{public_id}/publish
```

发布接口必须校验证据引用、结果完整性和权限；“同步通知团队”应生成独立通知投递任务，不能把发布事务与外部发送混为一个成功状态。

验收：P11–P13 所有进度和活动可回读；pause/resume/cancel/retry 幂等；发布版本不可被静默覆盖；每条结论能追溯证据。

### BE-04：监控计划、运行详情与分析队列（P1）

新增稳定的用户级 `MonitoringPlan`，由它编排现有 ProbeTask，而不是把 probe plan 响应直接冒充 PLAN 实体。

模型建议：

- `MonitoringPlan(public_id, name, owner_id, enabled, schedule, timezone, query_config, source_ids, version...)`
- `PlanRunRequest(idempotency_key, plan_id, requested_by, reason, run_id...)`
- 扩展 `CollectionRun` 的 public ID、stage events、log references、outputs 和关联对象。
- 为 `AlertEvaluationQueue` / analysis queue 暴露安全的只读 task view 与受控动作。

建议接口：

```text
GET/POST /api/v1/monitoring-plans
GET/PATCH /api/v1/monitoring-plans/{public_id}
POST      /api/v1/monitoring-plans/{public_id}/actions/{pause|resume}
POST      /api/v1/monitoring-plans/{public_id}/runs
GET       /api/v1/runs
GET       /api/v1/runs/{public_id}
GET       /api/v1/runs/{public_id}/events
GET       /api/v1/runs/{public_id}/logs
GET       /api/v1/runs/{public_id}/outputs
POST      /api/v1/runs/{public_id}/retry
GET       /api/v1/analysis-queue/tasks
GET       /api/v1/analysis-queue/tasks/{id}
PATCH     /api/v1/analysis-queue/tasks/{id}/priority
POST      /api/v1/analysis-queue/tasks/{id}/retry
POST      /api/v1/analysis-queue/tasks/{id}/cancel
```

日志应分页/流式并做敏感信息清洗；output 只返回受控元数据和下载 token。run-now/retry 返回 202 + `run_id`，前端轮询/订阅状态，不能立即显示“执行成功”。

验收：P17–P21 不再从多份不等价数据拼装假实体；同一幂等键不会重复启动运行；失败运行可追溯到 stage、错误、日志和输出。

### BE-05：来源目录、配置与健康历史（P1）

当前 connector registry 主要由代码/环境配置驱动。产品 UI 若要编辑来源，需要明确哪些字段可在线修改，哪些仍由部署管理。

新增/扩展：

- `SourceDefinition`：display_name、type、enabled、query capability、schedule defaults、config schema/version。
- `SourceCredentialRef`：只保存 secret manager 引用，不回显明文。
- `SourceHealthSample` / `SourceIncident`：历史可查询并关联 run/error。
- 配置变更 draft、validate、activate 流程；不能一次 PATCH 直接破坏生产 connector。

建议接口：

```text
GET       /api/v1/sources/{source_id}
POST      /api/v1/sources                         # 仅支持可动态创建的 connector 类型
PATCH     /api/v1/sources/{source_id}
POST      /api/v1/sources/{source_id}/validate
POST      /api/v1/sources/{source_id}/test-runs
GET       /api/v1/sources/{source_id}/health-series
GET       /api/v1/sources/{source_id}/incidents
GET       /api/v1/sources/{source_id}/runs
GET       /api/v1/sources/{source_id}/observations
POST      /api/v1/sources/actions/sync             # admin + explicit source_ids
```

验收：P14–P16 所有统计来自同一时间窗；测试运行与正式运行分开标记；密钥不出现在 response、日志或审计 detail。

### BE-06：告警规则、通知中心与偏好（P1/P2）

在现有 rule/event 基础上补齐：

```text
DELETE /api/v1/alerts/rules/{id}
POST   /api/v1/alerts/rules/{id}/test              # dry-run，不创建真实告警，或明确 test event
POST   /api/v1/alerts/events/batch-status
GET    /api/v1/notifications
PATCH  /api/v1/notifications/{id}
GET    /api/v1/notification-preferences
PATCH  /api/v1/notification-preferences
```

规则模板可作为只读 `GET /alerts/rule-templates`，不要硬编码在 UI。通知与 AlertEvent 分开：通知是用户投递/已读视图，告警是业务事件。邮件/Webhook 的 queued/sent/failed 状态需要在 UI 明确展示。

验收：P22–P23 和顶栏未读数由真实数据驱动；批量动作逐项返回结果；规则 test 不污染生产事件统计。

### BE-07：工作区、成员邀请、RBAC、账户安全与集成（P1/P2）

拆分为四个安全边界：

1. Workspace：基本信息、logo asset reference、领域偏好、retention policy。导出/清理/删除必须是异步高风险 job，并要求 owner 再认证。
2. Membership：邀请 token、过期、接受、撤销、重发；不要通过“创建一个带临时密码的 User”模拟邀请。
3. Account security：self password change、session list/revoke、MFA TOTP、恢复码、Passkey、email/phone verification、account deletion request。
4. Integration：catalog、installation、OAuth state/PKCE、credential reference、connection test、health。Webhook 保留为一种 integration adapter。

建议接口组：

```text
GET/PATCH /api/v1/workspace
POST      /api/v1/workspace/logo
POST      /api/v1/workspace/export-jobs
POST      /api/v1/workspace/cleanup-jobs
POST      /api/v1/workspace/deletion-requests

GET/POST  /api/v1/member-invitations
POST      /api/v1/member-invitations/{id}/resend
DELETE    /api/v1/member-invitations/{id}
POST      /api/v1/member-invitations/{token}/accept

GET       /api/v1/rbac/roles
GET       /api/v1/rbac/permissions
GET       /api/v1/account/sessions
DELETE    /api/v1/account/sessions/{id}
POST      /api/v1/account/sessions/revoke-others
POST      /api/v1/account/password-change
POST      /api/v1/account/password-reset-requests
POST      /api/v1/account/password-resets
POST      /api/v1/account/mfa/totp/enroll
POST      /api/v1/account/mfa/totp/confirm
DELETE    /api/v1/account/mfa/totp
POST      /api/v1/account/recovery-codes/rotate

GET       /api/v1/integrations/catalog
GET/POST  /api/v1/integrations/installations
POST      /api/v1/integrations/installations/{id}/oauth/start
GET       /api/v1/integrations/oauth/callback
POST      /api/v1/integrations/installations/{id}/test
DELETE    /api/v1/integrations/installations/{id}

POST      /api/v1/access-requests
GET/PATCH /api/v1/admin/access-requests/{id}
```

角色决策：当前四种内置角色可以先通过只读 API 返回。除非产品明确需要自定义角色，不实现 P26 的“编辑内置角色”；UI 应改为只读矩阵。若确需自定义角色，另建 Role/Permission/RoleBinding 模型，内置 OWNER 权限不可删除，继续保留最后 OWNER 并发不变量。

MFA/SSO/Passkey 不应一次性同时开发。优先 TOTP + session revoke + password reset；企业 SSO 和 WebAuthn 作为独立安全评审包。

验收：所有敏感动作要求近期认证或 step-up；恢复码只显示一次且哈希存储；OAuth state 一次性且有过期时间；秘密永不回显；所有管理员变化进入审计。

### BE-08：全局搜索、审计、诊断与统一导出（P1/P2）

建议接口：

```text
GET  /api/v1/search?q=...&types=...&cursor=...
GET  /api/v1/audit/{id}
GET  /api/v1/audit?actor=...&resource=...&status_code=...&from=...&to=...&cursor=...
POST /api/v1/export-jobs
GET  /api/v1/export-jobs/{id}
GET  /api/v1/diagnostics
POST /api/v1/diagnostic-runs
GET  /api/v1/diagnostic-runs/{id}
```

全局搜索结果使用统一 envelope：`type/public_id/title/snippet/highlights/updated_at/target_url/score`，在 SQL 层执行权限裁剪；不要先取全量数据再由前端过滤。搜索第一阶段可聚合 observations、opportunities、keywords，Research/Run 在对应模块上线后接入。

导出改为 job，body 明确 resource、format、filter、selected_fields。下载使用短期授权 URL，并记录导出人、过滤条件、行数、数据分类和 hash。

诊断接口只暴露可公开给当前角色的聚合状态，不返回环境变量、连接串、token、内部堆栈或未清洗日志。主动测试必须是 admin 异步 job，并有频率限制。

验收：P29–P31 使用服务端分页和权限裁剪；大导出不阻塞 API worker；诊断报告经过 secret scan；每个搜索结果可直接到真实实体。

## 5. 横切契约

所有新增 API 遵守以下规则：

### 分页

列表统一使用 cursor，response 至少为：

```json
{
  "items": [],
  "next_cursor": null,
  "has_more": false,
  "total": null
}
```

`total` 对大表可为空；不要让 UI 依赖代价昂贵的精确总数。

### 幂等与并发

- create/run/retry/publish/invite/export 使用 `Idempotency-Key`。
- 用户可编辑资源返回 `version` 或 ETag；PATCH 使用 `If-Match`，冲突返回 409。
- 状态动作由服务端校验状态机，不接受任意字符串。

### 异步任务

- 预计超过普通请求时限的动作返回 202 + job/run public ID。
- job 至少有 QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED，带 progress、retryable、error code。
- UI 的“任务已创建”与“业务已完成”必须使用不同文案。

### RBAC 与审计

- read/write/admin 只是最低层 scope；高风险动作增加 owner 或专用 permission。
- 审计 actor 来自服务端 principal，不信任客户端传入。
- 审计保存对象 public ID、动作、结果和最小必要 diff；敏感字段脱敏。

### 证据与数据来源

- 自动、人工、mock、synthetic 数据必须显式标记。
- 研究、分析、告警和机会评分的结果都能回溯 evidence ID、模型/算法版本和时间窗。
- production API 不返回原型 mock ID 或 mock 业务记录。

## 6. 推荐交付顺序

1. **M0 可运行外壳**：BE-00；React production entry、deep link、auth/bootstrap、public ID 决策。
2. **M1 核心读闭环**：BE-01 + BE-02 的 read/detail；打通 P01–P10，先消除核心 mock。
3. **M2 核心写闭环**：机会创建/状态/负责人/证据/分析 revision；所有写成功可回读。
4. **M3 研究闭环**：BE-03；打通 P11–P13。
5. **M4 采集运营闭环**：BE-04 + BE-05；打通 P14–P21。
6. **M5 告警与治理**：BE-06 + BE-08；打通告警、搜索、审计和诊断。
7. **M6 组织与安全**：BE-07；先 workspace/invite/session/TOTP，再评审 SSO/Passkey/custom roles/integrations。

每个里程碑的完成条件不是“页面能打开”，而是：无生产 mock、真实权限、失败可恢复、状态可回读、审计可追溯、契约测试通过。

## 7. 建议暂缓或改为只读的原型动作

在对应后端完成前，以下动作不应继续显示成功 toast：

- 修改机会生命周期、负责人和人工证据关系。
- 研究的新建、暂停、取消、重试和发布。
- 监控计划创建/编辑/暂停/立即运行，以及运行重试。
- 来源连接、编辑、批量同步和在线密钥配置。
- 工作区清理、重置、删除。
- 邀请/重发邀请、编辑角色权限。
- 修改密码、邮箱、手机、MFA、Passkey、会话注销、删除账户。
- OAuth 修复、集成测试、发送 Slack 测试消息。
- 导出 PDF/Excel/诊断包，除非实际下载任务已经创建并可查询。
- “人工客服已接入”“密码重置邮件已发送”等不存在的外部动作。

安全 fallback 顺序：隐藏不成立的动作 > 明确只读 > 禁用并解释 > 显示能力未开放状态。
