# Opportunity Radar 完整产品要求

## 产品目标

持续发现用户原本不知道应该搜索的信息差机会，并把零散的需求、供给、执行与风险信号组织成可追溯的研究对象。

## 核心用户闭环

1. 用户配置主动关注主题与数据源。
2. 系统周期执行 Probe，同时接收 Feed / Import / Instrumented Observation。
3. 新 Observation 进入关键词发现、趋势和关系图。
4. 相关关键词聚合成 Opportunity。
5. 规则引擎评分，结构化分析补充目标用户、商业模式、变现路径和风险。
6. Alert Rule 把达到阈值的机会推入内部 Inbox。
7. 用户收藏、进入 REVIEWING / TRACKING、记录备注和标签。
8. 新证据持续更新同一 Opportunity，系统再次触发分析和预警。
9. 用户可导出研究结果与原始证据，所有写操作有审计记录。

## 完整产品模块

### Discovery
- Source Registry
- Connector Runtime
- Watch Keywords
- Probe Planner
- Scheduler / Worker
- Raw Observation
- Normalization / Deduplication

### Intelligence
- Keyword Discovery
- Keyword Lifecycle
- Trend Engine
- Keyword Graph
- Opportunity Clustering
- Deterministic Scoring
- Structured Analysis
- Evidence Provenance

### Research Workspace
- Opportunity Inbox
- Search / Filter
- Star / Priority
- Research Status
- Tags / Notes
- Evidence Detail
- CSV Export

### Alerting
- Alert Rules
- Alert Evaluation
- Internal Alert Inbox
- Event Acknowledge / Dismiss
- 后续：邮件 / Webhook / IM 通知渠道

### Operations
- Source Enable / Disable
- Source Health / Circuit Breaker
- Probe Tasks
- Collection Runs
- Analysis Queue
- Request Audit
- Backup / Restore
- Readiness / Migration validation

### Security
- Production API Key authentication
- Read/write authentication modes
- Request ID
- Mutation audit
- Sensitive App Observation sanitizer
- Production PostgreSQL requirement

## 非目标/禁止实现

授权 App Observation 仅用于正常可见数据的研究采样。产品不实现认证绕过、验证码绕过、设备风控规避、付费权限绕过、私人数据访问或批量账号对抗。
