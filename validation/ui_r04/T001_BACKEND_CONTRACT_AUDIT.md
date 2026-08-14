# T001 — R04 后端能力与 UI 契约审计

状态：**PASS**（2026-08-14）

本任务只做契约审计，不修改后端业务接口，不实现业务视觉页面。UI 依赖以 R04 Development Pack 的 `04_MANIFESTS/001_UI_DEVELOPMENT_ORDER.csv` 为准；PNG/HTML 仅作为状态和结构参考，未将 HTML mock 字段当成业务事实。

## 审计证据

- 路由入口：`backend/app/main.py`、`backend/app/api/auth.py`、`backend/app/api/routes.py`、`backend/app/api/operations.py`、`backend/app/api/research.py`、`backend/app/api/scoring.py`。
- 数据与状态：`backend/app/db/models.py`、`backend/app/domain/schemas.py`、`backend/app/domain/webhook.py`。
- 服务语义：`backend/app/services/opportunities.py`、`research.py`、`probes.py`、`analysis_queue.py`、`alerts.py`、`auth.py`、`source_preferences.py`、`webhook_endpoints.py`。
- 前端可复用非视觉契约：`frontend/src/client.ts`、`frontend/src/router.ts`、`frontend/src/permissions.ts`；当前 `screens.ts/shell.ts/theme.ts/ui.ts` 的旧 R02 视觉实现不作为 R04 设计依据。
- 机器可追溯登记：`_taskbooks/Opportunity_Radar_R04_Development_Pack_v1.0/03_REGISTRIES/001_BACKEND_INTERFACE_GAPS.csv`。

## 已确认的真实 API 契约

| 能力 | 真实接口与权限 | R04 处理 |
|---|---|---|
| 登录/当前身份 | `GET /api/v1/auth/config`、`POST /api/v1/auth/login`、`POST /api/v1/auth/logout`、`GET /api/v1/auth/me`；写操作受 session/CSRF 或配置模式约束 | 接真实接口；登录失败、未授权、找不到对象走明确错误态 |
| 工作台 | `GET /api/v1/dashboard` | 接真实摘要；不从 AppShell 示例按钮派生写能力 |
| 机会 | `GET /api/v1/opportunities/page`、`GET /api/v1/opportunities`、`GET /api/v1/opportunities/{id}` | 接真实分页、筛选、详情、证据字段；`stage` 只读 |
| 机会研究状态 | `PATCH /api/v1/opportunities/{id}/research`；字段 `status/starred/priority/notes/tags` | 仅接真实研究状态；不等同于研究生成 |
| 情报/证据 | `GET /api/v1/observations`；机会详情返回真实 evidence/citations 字段 | 只展示 API 返回字段；无独立资源的详情 Tab 降级 |
| 关键词/趋势/图谱 | `GET /api/v1/keywords`、`GET /api/v1/keywords/{id}/trend`、`GET /api/v1/keyword-graph`、`GET/POST/PATCH /api/v1/watch-keywords` | 接真实关键词和图谱读取；写操作按 schema/权限接线 |
| 数据源/运行 | `GET /api/v1/sources`、`GET /api/v1/sources/health`、`GET /api/v1/collection-runs`、`GET /api/v1/probes/plan`；管理员额外有 probe sync/run-due | 读取真实状态；内部同步/到期运行不作为页面立即运行按钮 |
| 告警/规则 | `GET/PATCH /api/v1/alerts/events/{id}`、`GET/POST/PATCH /api/v1/alerts/rules` | 状态和规则字段可接真实写 API；无 read/unread 独立语义 |
| 用户/角色 | `GET/POST/PATCH /api/v1/admin/users`；OWNER 约束由服务端执行 | 接真实管理员写操作；权限不足显示 403/禁用，不本地改状态 |
| 审计/诊断 | `GET /api/v1/audit`、`GET /health`、`GET /ready`、`GET /api/v1/sources/health`、provider 读取接口 | 接真实只读检查；失败保留错误证据 |
| 个人令牌 | `GET/POST /api/v1/auth/tokens`、`DELETE /api/v1/auth/tokens/{id}` | 接真实令牌流程；secret 仅在创建响应中显示一次 |
| Webhook 集成 | `GET/POST/PATCH/DELETE /api/v1/webhooks/endpoints`；secret 写入但不回显 | 仅按已确认 Webhook 契约接线，不扩展成通用集成 |
| 来源偏好 | `PATCH /api/v1/sources/{source_id}/preference`，字段 `enabled/note` | 只接确认字段；隐藏 restore/reorder 等未确认动作 |

## 65 个 UI 状态逐项核对

下表中的 `MATCHED` 表示存在可安全接线的真实读取或写入；`CONTRACT_MISMATCH` 表示有部分相关能力但字段/对象/语义不等价；`DEFERRED_UNAVAILABLE` 表示没有安全 API；`UI_ONLY` 表示路由或错误态无需业务 API。具体证据和 fallback 以缺口登记表为准。

| UI | 状态 | 真实契约/证据 | 安全 fallback |
|---|---|---|---|
| U001 | UI_ONLY | AppShell 参考，不是业务路由 | 只复用外壳规范，不实现示例按钮 |
| U002 | MATCHED | auth config/login/me | 401/429 错误态 |
| U003 | DEFERRED_UNAVAILABLE | 无密码重置接口 | 帮助说明并返回登录 |
| U004 | UI_ONLY | 403 权限状态由路由/HTTP 错误决定 | 返回上一页或工作台 |
| U005 | UI_ONLY | 404 对象状态由路由/API 404 决定 | 返回来源列表 |
| U006 | CONTRACT_MISMATCH | opportunities/page + observations + keywords，无统一搜索资源 | 并行读取真实分类，隐藏无目标分类 |
| U007 | DEFERRED_UNAVAILABLE | 无 notification 资源 | 空态/业务告警入口，不伪造未读数 |
| U008 | UI_ONLY | 帮助内容与安全导航 | 诊断、账号、错误页真实落点 |
| U009 | MATCHED | GET /api/v1/dashboard | 真实摘要加载失败显示局部错误态 |
| U010 | MATCHED | GET /api/v1/opportunities/page | 真实筛选、分页和空态 |
| U011 | MATCHED | GET /api/v1/opportunities/{id} | 详情 404/只读 stage |
| U012 | MATCHED | opportunity_detail 的 evidence/citations 字段 | 仅展示返回的证据 |
| U013 | CAPABILITY_NOT_EXPOSED | 机会 analysis 字段可读；生成不等价 | 只读已有分析，隐藏生成 |
| U014 | CONTRACT_MISMATCH | scoring history 只有评分快照 | 只读评分历史，隐藏完整生命周期事件 |
| U015 | MATCHED | GET /api/v1/observations | 真实列表/筛选/分页 |
| U016 | CONTRACT_MISMATCH | observation 列表字段可读，无独立情报详情资源 | 展示返回字段并提供来源路径 |
| U017 | DEFERRED_UNAVAILABLE | 无 raw evidence detail 资源 | 能力说明 + 返回情报 |
| U018 | DEFERRED_UNAVAILABLE | 无 intelligence relationship 资源 | 能力说明 + 关键词图谱入口 |
| U019 | DEFERRED_UNAVAILABLE | 无 processing trace 资源 | 能力说明 + 运行/来源入口 |
| U020 | MATCHED | keywords/trend/graph 真实读取 | 无数据时空态 |
| U021 | MATCHED | watch-keywords GET/POST/PATCH | 后端错误态，不本地假成功 |
| U022 | MATCHED | keyword trend 与 weekly trend 读取 | 只展示已有报告 |
| U023 | MATCHED | GET /api/v1/keyword-graph | 真实节点/边；无节点空态 |
| U024 | DEFERRED_UNAVAILABLE | 无 StructuredAnalysis 列表资源 | 展示可读机会分析或能力说明 |
| U025 | DEFERRED_UNAVAILABLE | 无 ResearchTask 列表资源 | 空态带返回路径 |
| U026 | DEFERRED_UNAVAILABLE | 无 ResearchResult 列表资源 | 空态带返回路径 |
| U027 | DEFERRED_UNAVAILABLE | 无研究结果结论详情资源 | 只读能力说明 |
| U028 | DEFERRED_UNAVAILABLE | 无研究结果证据资源 | 只读能力说明 |
| U029 | DEFERRED_UNAVAILABLE | 无研究结果方法资源 | 只读能力说明 |
| U030 | DEFERRED_UNAVAILABLE | 无研究结果活动资源 | 只读能力说明 |
| U031 | DEFERRED_UNAVAILABLE | 无研究任务简报资源 | 只读能力说明 |
| U032 | DEFERRED_UNAVAILABLE | 无研究任务证据资源 | 只读能力说明 |
| U033 | DEFERRED_UNAVAILABLE | 无研究任务发现资源 | 只读能力说明 |
| U034 | DEFERRED_UNAVAILABLE | 无研究任务活动资源 | 只读能力说明 |
| U035 | DEFERRED_UNAVAILABLE | 无结构化分析结论资源 | 只读能力说明 |
| U036 | DEFERRED_UNAVAILABLE | 无结构化分析证据矩阵资源 | 只读能力说明 |
| U037 | DEFERRED_UNAVAILABLE | 无结构化分析处理轨迹资源 | 只读能力说明 |
| U038 | MATCHED | GET /api/v1/sources | 真实 source registry 列表 |
| U039 | CONTRACT_MISMATCH | sources 有 descriptor，无独立 detail 资源 | 展示已确认 descriptor 字段 |
| U040 | MATCHED | collection-runs 可按 source_id 读取 | 运行列表空态 |
| U041 | CONTRACT_MISMATCH | run summary 有产出计数，无 outputs 资源 | 展示 summary，隐藏下载/详情动作 |
| U042 | CONTRACT_MISMATCH | health/run 有 error 字段，无 source error 资源 | 展示已有 error，隐藏扩展字段 |
| U043 | CONTRACT_MISMATCH | probes/plan 与 tasks 可读，控制语义不等价 | 只读计划和任务 |
| U044 | CONTRACT_MISMATCH | 无监控计划 detail/update 资源 | 只读计划/最近运行 |
| U045 | MATCHED | GET /api/v1/collection-runs | 真实列表、筛选、分页 |
| U046 | MATCHED | collection run summary 字段 | 真实摘要和 404 |
| U047 | DEFERRED_UNAVAILABLE | 无 run log 资源 | 能力说明，保留返回 |
| U048 | DEFERRED_UNAVAILABLE | 无 run output 资源 | 能力说明，展示 summary |
| U049 | DEFERRED_UNAVAILABLE | 无 related object 资源 | 隐藏猜测链接 |
| U050 | CONTRACT_MISMATCH | 可从 opportunities.analysis_status 派生只读队列 | 隐藏重试/取消 |
| U051 | MATCHED | alerts/events GET 与真实关联字段 | 只读告警列表和下钻 |
| U052 | MATCHED | alerts/rules GET/POST/PATCH | 接真实字段，隐藏删除/测试 |
| U053 | MATCHED | admin users GET/POST/PATCH | 受服务端权限保护 |
| U054 | CONTRACT_MISMATCH | role/scopes 可读，无完整权限矩阵资源 | 只读角色权限枚举 |
| U055 | MATCHED | GET /api/v1/audit | 管理权限错误态 |
| U056 | DEFERRED_UNAVAILABLE | 无 general settings 资源 | 只读配置来源说明 |
| U057 | DEFERRED_UNAVAILABLE | auth config 不等于 security settings | 隐藏策略保存 |
| U058 | DEFERRED_UNAVAILABLE | 无 notification settings 资源 | 不可配置提示 |
| U059 | CONTRACT_MISMATCH | Webhook endpoint 资源存在，通用集成不存在 | 仅接 Webhook 字段 |
| U060 | MATCHED | sources + source preference PATCH | 仅 enabled/note，可读权限错误 |
| U061 | MATCHED | health/ready/source health/provider read | 分项显示失败原因 |
| U062 | CONTRACT_MISMATCH | auth/me 读当前用户，无 profile/password PATCH | 读资料；隐藏未确认写操作 |
| U063 | DEFERRED_UNAVAILABLE | 无 MFA 资源 | 说明后端未提供 |
| U064 | DEFERRED_UNAVAILABLE | 无 active session list/revoke 资源 | 说明后端未提供 |
| U065 | MATCHED | auth tokens GET/POST/DELETE | secret 只显示一次，撤销走真实 API |

## 结论与实现约束

1. 读取能力优先使用真实 API 返回的字段、分页和状态；不使用 PNG/HTML 示例数字作为事实。
2. 所有缺口已写入 R04 `001_BACKEND_INTERFACE_GAPS.csv`，包含证据、分类和 UI fallback。
3. 后续 T002 起每个任务在接线前继续对局部契约复核；缺口不阻塞 UI、路由、Docker 或浏览器验收。
4. R04 页面实现必须隐藏伪写按钮，或显示明确只读/能力不可用说明；禁止本地状态变更后提示保存成功。
