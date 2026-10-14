# React 页面—能力—接口追踪矩阵

日期：2026-09-04  
维护规则：每个可点击动作必须在此矩阵标为 `真实接口`、`UI-only`、`只读`、`隐藏/禁用` 或 `待开发`。未有服务端契约时，禁止显示成功 toast。

状态：`PRESENT` 可直接复用；`PARTIAL` 需适配/补字段；`MISSING` 必须先开发；`UI-only` 不持久化。

| 页面 | 读/写能力 | 当前状态 | 首选接口或目标契约 | 权限 | UI 落地状态 | 后端包 |
|---|---|---|---|---|---|---|
| P01 今日雷达 | KPI、趋势、告警、系统摘要 | PARTIAL | `GET /dashboard`；统一时间窗摘要 | read | 只读，行动项待接口 | BE-01/03/08 |
| P02 情报列表 | 检索、筛选、收藏、订阅 | PARTIAL | `GET /observations`；bookmark/subscription | read/write | 收藏/订阅待开发 | BE-01 |
| P03 情报详情 | 阅读、忽略、转机会、监控、导出 | PARTIAL | `GET /observations/{public_id}`；actions | read/write | 详情/写动作待开发 | BE-01/02/04 |
| P04 关键词发现 | 候选评估、忽略、合并、关注 | PARTIAL | keywords/watch；dismiss/merge | read/write/admin | 合并和评估待开发 | BE-01 |
| P05 关注关键词 | 新增、暂停、优先级、趋势 | PARTIAL | `watch-keywords` | read/write | 删除和显示偏好待开发 | BE-01 |
| P06 趋势分析 | 多词比较、异常、导出 | PARTIAL | trend；`/trends/compare` | read | 比较/导出待开发 | BE-01/08 |
| P07 关系图谱 | 图谱、实体聚焦、快照 | PARTIAL | keyword graph；entity graph | read | 实体图待开发 | BE-01/02 |
| P08 机会池 | 分页、筛选、关注、导出 | PARTIAL | opportunities page/CSV；watchers | read/write | 收藏待开发 | BE-02 |
| P09 机会详情 | 状态、负责人、证据、备注、下一步 | PARTIAL | opportunity detail/research；workflow fields | read/write | 写动作待开发 | BE-02/03 |
| P10 结构化分析 | 评分、编辑、版本、导出 | PARTIAL | analysis revisions/runs | read/write | 编辑/发布待开发 | BE-02/08 |
| P11 研究工作流 | 新建、筛选、进度、负责人 | MISSING | research workflows | read/write | 隐藏写动作直到可用 | BE-03 |
| P12 研究详情 | 步骤、暂停、恢复、取消、重试 | MISSING | research workflow actions/steps | read/write | 隐藏动作直到可用 | BE-03 |
| P13 研究结论 | 阅读、发布、通知、导出 | MISSING | research results/publish | read/write | 隐藏动作直到可用 | BE-03/08 |
| P14 来源管理 | 目录、连接、编辑、启停、同步 | PARTIAL | sources/health/preference；source config | read/write | 连接/同步待开发 | BE-05 |
| P15 来源详情 | 配置、统计、运行、关联计划 | PARTIAL | source detail/run-now | read/write | 待开发 | BE-05/04 |
| P16 来源健康 | 分数、历史、异常、刷新 | PARTIAL | source health history | read | 历史待开发 | BE-05/08 |
| P17 监控计划 | CRUD、模板、启停、运行 | MISSING | monitoring plans | read/write | 隐藏动作直到可用 | BE-04 |
| P18 计划详情 | 配置、来源、统计、手动运行 | MISSING | monitoring plan detail/run | read/write | 隐藏动作直到可用 | BE-04 |
| P19 运行记录 | 查询、导出、日志、复跑 | PARTIAL | collection runs + export | read/write | 详情/复跑待开发 | BE-04/08 |
| P20 运行详情 | 阶段、日志、产出、错误、重试 | MISSING | run detail/log/output/retry | read/write | 隐藏动作直到可用 | BE-04 |
| P21 分析队列 | 队列、优先级、失败处理、控制 | PARTIAL | analysis queue controls | admin | 单项控制待开发 | BE-04 |
| P22 告警中心 | 列表、处理、批量、导出 | PARTIAL | alerts events；batch/export | read/write | 批量/导出待开发 | BE-06/08 |
| P23 告警规则 | CRUD、模板、测试、导出 | PARTIAL | alert rules；test/delete | read/write | 测试/删除待开发 | BE-06/08 |
| P24 工作区设置 | 设置、导出、清理、删除 | MISSING | workspace resource | admin | 高风险按钮禁用 | BE-07 |
| P25 成员管理 | 成员、邀请、重发、角色、导出 | PARTIAL | admin users；invitations | admin | 邀请生命周期待开发 | BE-07/08 |
| P26 角色权限 | 矩阵、编辑、复制模板 | PARTIAL | fixed RBAC；role matrix | admin | 自定义角色待决策 | BE-07 |
| P27 账户安全 | 资料、MFA、Passkey、Token、会话 | PARTIAL | auth/me/tokens；security methods | read/write | MFA/会话待开发 | BE-07 |
| P28 外部集成 | 目录、OAuth、测试、密钥引用 | MISSING | integrations/OAuth | admin | webhook 仅可只读复用 | BE-07 |
| P29 审计日志 | 检索、详情、导出 | PARTIAL | audit filters/detail/export | admin | 过滤/导出待开发 | BE-08 |
| P30 系统诊断 | 健康、检查、报告 | PARTIAL | health/ready/workers；diagnostics | admin | 受控检查待开发 | BE-08 |
| P31 全局搜索 | 跨对象搜索、保存搜索 | PARTIAL | global search/saved searches | read | 结果只能只读 | BE-08 |
| P32 登录 | 密码、MFA、SSO、找回 | PARTIAL | auth login；MFA/SSO/reset | public | 密码可接；其他待开发 | BE-07 |
| P33 无权限 | 说明、返回、申请权限 | UI-only/PARTIAL | 403 UI；access request | authenticated | 申请权限待开发 | BE-07 |
| P34 404 | 推荐入口、搜索、帮助 | UI-only/PARTIAL | UI；global search | public | 搜索依赖 BE-08 | BE-08 |

完整的字段、模型、幂等、并发、审计和错误语义以 [后端开发计划](REACT_PROTOTYPE_BACKEND_DEVELOPMENT_PLAN.md) 为准。本矩阵只定义页面接入决策，不能替代 OpenAPI 契约。
