# Opportunity Radar R02 — UI 页面元数据与实现合同

- Stitch Project ID: `15618650520496122485`
- Design System: `assets/02cc745e832d4c89bd705650673b1210`
- 主 Screen: **34**

## 不可违反的边界

- 仅 UI 重构：`backend_change=false`。
- 不修改 API 契约/业务语义/DB/Worker/调度/评分/告警/审计/Auth/RBAC。
- 未确认写操作必须隐藏，不得为原型补后端。
- `CONFIRMED_CAPABILITY`=能力此前 Review 已确认；精确 method/path 仍需最新源码绑定。
- `VERIFY_LATEST`=正式实现前从最新源码核对。
- 精确已确认路径仅 `GET /health`、`GET /ready`。
- Stitch 中所有示例数据/版本/URL/provider/字段值均为视觉 mock，不是实现事实。

## P01 — 登录

- Screen ID: `6e1f72c8cdc944e4929adaae6affd73b`
- Route: `VERIFY_LATEST`
- 状态: 默认, 输入错误, 登录中, 认证错误, 429限流, 服务异常

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 登录 | API | `auth.login` | CONFIRMED_CAPABILITY | 成功->P02；精确method/path VERIFY_LATEST |
| 显示/隐藏密码 | UI_ONLY | `toggle-password` | UI_ONLY |  |

## P02 — Dashboard 总览

- Screen ID: `721146f092ba449599cbc55e508916cd`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, Empty, Partial, Error, Refreshing

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `dashboard.read/aggregate` | VERIFY_LATEST | 不为UI新增聚合后端 |
| 查看全部机会 | NAVIGATE | `P12` | UI_ONLY |  |
| 机会行 | NAVIGATE | `P13` | UI_ONLY |  |
| 来源健康 | NAVIGATE | `P19` | UI_ONLY |  |
| 最近运行 | NAVIGATE | `P22` | UI_ONLY |  |
| 最近告警 | NAVIGATE | `P24` | UI_ONLY |  |
| 全局搜索 | NAVIGATE | `P03` | UI_ONLY |  |

## P03 — 全局搜索

- Screen ID: `0ad90df2dfb0462ab34c790f5bd26d21`
- Route: `VERIFY_LATEST`
- 状态: Initial, Loading, Normal, No Result, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 提交搜索 | API | `global_search_or_frontend_aggregate` | VERIFY_LATEST | 无统一搜索API时前端聚合现有查询，不新增后端 |
| 清空/分类筛选 | UI_ONLY | `local-search-state` | UI_ONLY |  |
| Opportunity结果 | NAVIGATE | `P13` | UI_ONLY |  |
| Observation结果 | NAVIGATE | `P07` | UI_ONLY |  |
| Keyword结果 | NAVIGATE | `P10/P09` | UI_ONLY |  |
| Research结果 | NAVIGATE | `P16/P17` | UI_ONLY |  |

## P04 — 403 无权限

- Screen ID: `f95504c1f6594644869c58a07066c704`
- Route: `VERIFY_LATEST`
- 状态: Forbidden

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回总览 | NAVIGATE | `P02` | UI_ONLY |  |
| 返回上一页 | UI_ONLY | `history.back` | UI_ONLY |  |

## P05 — 404 / 对象不存在

- Screen ID: `a9c5ad0f8d144a188ee6892237540268`
- Route: `VERIFY_LATEST`
- 状态: Not Found, Object Deleted

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回总览 | NAVIGATE | `P02` | UI_ONLY |  |
| 返回上一页 | UI_ONLY | `history.back` | UI_ONLY |  |
| 返回列表 | NAVIGATE | `CONTEXT_LIST` | UI_ONLY | 按来源上下文 P06/P12/P15/P21 等 |

## P06 — 原始情报 Observation 列表

- Screen ID: `062c515c6d57447fbade5af202c9a3b1`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, Empty, No Result, Stale, Partial, Error, Refreshing

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `observation.list` | CONFIRMED_CAPABILITY | path VERIFY_LATEST |
| 筛选/排序/分页 | API | `observation.list.query` | VERIFY_LATEST |  |
| Observation行 | NAVIGATE | `P07` | UI_ONLY |  |
| Source | NAVIGATE | `P19` | UI_ONLY |  |
| Keyword | NAVIGATE | `P10/P09` | UI_ONLY |  |
| 关联机会 | NAVIGATE | `P13` | UI_ONLY |  |
| 打开原始来源 | EXTERNAL | `source_url` | EXTERNAL | Raw数据只读 |

## P07 — Observation 详情

- Screen ID: `e69878066b9149eba3665a08ca5c037e`
- Route: `VERIFY_LATEST`
- 状态: Normal, Raw Partial, Source Unavailable, URL Unreachable, Stale, Processing, Analysis Failed

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 查看来源 | NAVIGATE | `P19` | UI_ONLY |  |
| Keyword | NAVIGATE | `P10/P09` | UI_ONLY |  |
| 关联机会 | NAVIGATE | `P13` | UI_ONLY |  |
| 原始来源 | EXTERNAL | `source_url` | EXTERNAL |  |
| 返回列表 | NAVIGATE | `P06` | UI_ONLY |  |

## P08 — 关键词发现

- Screen ID: `57346fbcd8e04ee79322ce1719d2bb4f`
- Route: `VERIFY_LATEST`
- 状态: Discovery Running, Normal, Empty, No Result, Insufficient Data, Partial, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `keyword.discovery.read` | CONFIRMED_CAPABILITY |  |
| Keyword | NAVIGATE | `P10` | UI_ONLY |  |
| 查看证据 | NAVIGATE | `P06?keyword=...` | UI_ONLY |  |
| 加入/取消关注 | API | `watch_keyword.write` | HIDE_IF_UNSUPPORTED | 必须先核最新API |
| 关联机会 | NAVIGATE | `P12/P13` | UI_ONLY |  |

## P09 — 关注关键词

- Screen ID: `80c5171c27d644a59ef9a222a12c0cbd`
- Route: `VERIFY_LATEST`
- 状态: Active, Disabled, No Signal, Running, Warning, Failed, Empty, Saving, Validation Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 添加/编辑 | DRAWER | `Watch Keyword Editor` | UI_ONLY |  |
| 保存 | API | `watch_keyword.write` | HIDE_IF_UNSUPPORTED | 字段按现有schema |
| 启用/停用 | API | `watch_keyword.enable_disable` | HIDE_IF_UNSUPPORTED |  |
| 查看趋势 | NAVIGATE | `P10` | UI_ONLY |  |
| 查看证据 | NAVIGATE | `P06` | UI_ONLY |  |
| 运行记录 | NAVIGATE | `P21` | UI_ONLY |  |

## P10 — 趋势分析

- Screen ID: `54f882be4ee14ee38d30911a18b40b12`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, Insufficient Data, No Trend, Partial, Stale, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 时间范围 | API | `trend.read.window` | CONFIRMED_CAPABILITY | 实际窗口以API为准 |
| 查看证据 | NAVIGATE | `P06` | UI_ONLY |  |
| 关系图谱 | NAVIGATE | `P11` | UI_ONLY |  |
| 查看机会 | NAVIGATE | `P12/P13` | UI_ONLY |  |
| 关注关键词 | API | `watch_keyword.write` | HIDE_IF_UNSUPPORTED |  |

## P11 — 关系图谱

- Screen ID: `ad561de9f108498fa59eb36d83372ea5`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, No Relation, Insufficient Data, Graph Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 读取图谱 | API | `graph.read` | CONFIRMED_CAPABILITY |  |
| 缩放/平移 | UI_ONLY | `graph-canvas` | UI_ONLY |  |
| 点击节点 | DRAWER | `Graph Node Detail` | UI_ONLY |  |
| 节点筛选 | UI_ONLY | `filter-returned-data` | UI_ONLY | 后端不支持的筛选仅前端处理 |
| Observation | NAVIGATE | `P07` | UI_ONLY |  |
| 趋势 | NAVIGATE | `P10` | UI_ONLY |  |
| 机会 | NAVIGATE | `P13` | UI_ONLY |  |
| 来源 | NAVIGATE | `P19` | UI_ONLY |  |

## P12 — Opportunity 列表

- Screen ID: `1c9cbf41fe4c4fca88f1113abde76751`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, Empty, No Result, New, Analysis Pending, Analysis Failed, Partial, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `opportunity.list` | CONFIRMED_CAPABILITY |  |
| 筛选/排序/分页 | API | `opportunity.list.query` | VERIFY_LATEST |  |
| Opportunity行 | NAVIGATE | `P13` | UI_ONLY |  |
| 趋势 | NAVIGATE | `P10` | UI_ONLY |  |
| 证据/来源 | NAVIGATE | `P06/P19` | UI_ONLY |  |
| 导出 | API | `opportunity.export` | HIDE_IF_UNSUPPORTED |  |
| 归档/忽略/状态变更 | API | `opportunity.state_write` | HIDE_IF_UNSUPPORTED | 不得新增批量状态API |

## P13 — Opportunity 详情

- Screen ID: `bec8b94c93e04162a01d5e752e2646e7`
- Route: `VERIFY_LATEST`
- 状态: Analysis Pending, Running, Success, Failed, Evidence Partial, Stale, Research Not Started, Research Running, Research Completed, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 查看证据 | NAVIGATE | `P06/P07` | UI_ONLY |  |
| 查看趋势 | NAVIGATE | `P10` | UI_ONLY |  |
| 打开图谱 | NAVIGATE | `P11` | UI_ONLY |  |
| 完整分析 | NAVIGATE | `P14` | UI_ONLY |  |
| 开始研究 | API | `research.start` | HIDE_IF_UNSUPPORTED | 成功->P15/P16 |
| 研究任务 | NAVIGATE | `P16/P15` | UI_ONLY |  |
| 研究结果 | NAVIGATE | `P17` | UI_ONLY |  |
| 业务状态操作 | API | `opportunity.state_write` | HIDE_IF_UNSUPPORTED |  |

## P14 — 结构化分析

- Screen ID: `16885e1ecb8e4eb3b38b3fc7422a579a`
- Route: `VERIFY_LATEST`
- 状态: Not Generated, Queued, Running, Completed, Failed, Partial, Provider Unavailable

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回机会 | NAVIGATE | `P13` | UI_ONLY |  |
| 查看证据 | NAVIGATE | `P06/P07` | UI_ONLY |  |
| 开始/重新分析 | API | `analysis.enqueue_or_trigger` | HIDE_IF_UNSUPPORTED |  |
| 开始研究 | API | `research.start` | HIDE_IF_UNSUPPORTED | 成功->P15/P16 |

## P15 — Research Workflow 列表

- Screen ID: `207ed97119ee4d9bbd6b5ab0b1448685`
- Route: `VERIFY_LATEST`
- 状态: Queued, Running, Completed, Failed, Cancelled, Empty, Loading, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| Workflow | NAVIGATE | `P16` | UI_ONLY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| Result | NAVIGATE | `P17` | UI_ONLY |  |
| 重试 | API | `research.retry` | HIDE_IF_UNSUPPORTED |  |
| 取消 | API | `research.cancel` | HIDE_IF_UNSUPPORTED |  |

## P16 — Research Workflow 详情

- Screen ID: `4e8888bfbe474fe79ce2bc3596f827d9`
- Route: `VERIFY_LATEST`
- 状态: Pending, Running, Step Failed, Completed, Partial

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回列表 | NAVIGATE | `P15` | UI_ONLY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| 证据 | NAVIGATE | `P06/P07` | UI_ONLY |  |
| 结果 | NAVIGATE | `P17` | UI_ONLY |  |
| 重试失败步骤 | API | `research.retry_step` | HIDE_IF_UNSUPPORTED | Pause/Export Logs 禁止默认显示 |

## P17 — Research Result

- Screen ID: `b662a241ad154a52b50daa0e0862b264`
- Route: `VERIFY_LATEST`
- 状态: Completed, Partial Result, Stale Evidence, Unavailable

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回Workflow | NAVIGATE | `P16` | UI_ONLY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| 原始证据 | NAVIGATE | `P06/P07` | UI_ONLY |  |
| 导出 | API | `research.export` | HIDE_IF_UNSUPPORTED | 默认隐藏 |

## P18 — 来源管理

- Screen ID: `24dd5d3664c34c78a4a26cc287c74579`
- Route: `VERIFY_LATEST`
- 状态: Healthy, Warning, Failed, Disabled, Never Run, Running, Loading, Empty, Saving, Validation Error, Test Running, Test Success, Test Failed

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 添加/编辑 | DRAWER | `Source Editor` | UI_ONLY |  |
| 保存 | API | `source.write` | HIDE_IF_UNSUPPORTED | 字段严格按Source schema |
| 测试连接 | API | `source.connection_test` | HIDE_IF_UNSUPPORTED |  |
| 启用/停用 | API | `source.enable_disable` | HIDE_IF_UNSUPPORTED |  |
| 详情 | NAVIGATE | `P19` | UI_ONLY |  |
| 运行记录 | NAVIGATE | `P21` | UI_ONLY |  |

## P19 — 来源详情 / Source Health

- Screen ID: `445f1293d5054a64ba2e3288048f096a`
- Route: `VERIFY_LATEST`
- 状态: Healthy, Degraded, Failed, Disabled, Circuit Open, Recovering, Never Run, Loading, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 编辑来源 | DRAWER | `Source Editor` | UI_ONLY |  |
| 测试连接 | API | `source.connection_test` | HIDE_IF_UNSUPPORTED |  |
| 启用/停用 | API | `source.enable_disable` | HIDE_IF_UNSUPPORTED |  |
| 运行记录 | NAVIGATE | `P21` | UI_ONLY |  |
| Run | NAVIGATE | `P22` | UI_ONLY |  |
| 返回来源 | NAVIGATE | `P18` | UI_ONLY |  |

## P20 — 监控计划

- Screen ID: `eded87322e0a405bb82ab006dd5cf7a6`
- Route: `VERIFY_LATEST`
- 状态: Scheduled, Running, Healthy, Paused, Failed, Circuit Open, Empty, Loading, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 查看 | DRAWER | `Monitoring Plan Detail` | UI_ONLY |  |
| 运行记录 | NAVIGATE | `P21` | UI_ONLY |  |
| 最近Run | NAVIGATE | `P22` | UI_ONLY |  |
| Watch Target | NAVIGATE | `P09` | UI_ONLY |  |
| 暂停/恢复 | API | `planner.pause_resume` | HIDE_IF_UNSUPPORTED |  |
| 立即运行 | API | `planner.run_now` | HIDE_IF_UNSUPPORTED |  |

## P21 — 运行记录

- Screen ID: `ba402ddace5e40ea87ccae18a225939e`
- Route: `VERIFY_LATEST`
- 状态: Queued, Running, Success, Failed, Retrying, Cancelled, Loading, Empty, No Result, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `runs.list` | CONFIRMED_CAPABILITY |  |
| 筛选/分页 | API | `runs.list.query` | VERIFY_LATEST |  |
| Run行 | NAVIGATE | `P22` | UI_ONLY |  |
| Source | NAVIGATE | `P19` | UI_ONLY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| Research | NAVIGATE | `P16` | UI_ONLY |  |
| 重试 | API | `run.retry` | HIDE_IF_UNSUPPORTED |  |

## P22 — 运行详情

- Screen ID: `f33c6758520a4db2a64a4125e9c51f9b`
- Route: `VERIFY_LATEST`
- 状态: Queued, Running, Success, Failed, Retrying, Recovering, Partial

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 返回运行记录 | NAVIGATE | `P21` | UI_ONLY |  |
| Source | NAVIGATE | `P19` | UI_ONLY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| Research | NAVIGATE | `P16` | UI_ONLY |  |
| Observation | NAVIGATE | `P07` | UI_ONLY |  |
| 重试运行 | API | `run.retry` | HIDE_IF_UNSUPPORTED |  |
| 复制ID | UI_ONLY | `clipboard.copy` | UI_ONLY |  |

## P23 — Analysis Queue

- Screen ID: `490a0582b94440c7bf5396977ea654bd`
- Route: `VERIFY_LATEST`
- 状态: Healthy, Backlogged, Worker Unavailable, Failed Jobs, Empty, Loading, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `analysis_queue.read` | CONFIRMED_CAPABILITY |  |
| Opportunity | NAVIGATE | `P13` | UI_ONLY |  |
| Result | NAVIGATE | `P14` | UI_ONLY |  |
| 关联Run | NAVIGATE | `P22` | UI_ONLY |  |
| 重试 | API | `analysis_queue.retry` | HIDE_IF_UNSUPPORTED | 禁止清空队列/删除Job/改状态 |

## P24 — 告警收件箱

- Screen ID: `34f75d30372a4315bf5dcf1b2c969397`
- Route: `VERIFY_LATEST`
- 状态: Unread, Read, Pending, Delivered, Delivery Failed, Empty, Loading, No Result, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `alert_inbox.read` | CONFIRMED_CAPABILITY |  |
| 告警行 | DRAWER | `Alert Detail` | UI_ONLY |  |
| 查看机会 | NAVIGATE | `P13` | UI_ONLY |  |
| 查看规则 | NAVIGATE | `P25` | UI_ONLY |  |
| 标记已读/未读 | API | `alert_inbox.read_state_write` | HIDE_IF_UNSUPPORTED |  |
| 全部已读 | API | `alert_inbox.mark_all_read` | HIDE_IF_UNSUPPORTED |  |

## P25 — 告警规则

- Screen ID: `462f8e09e73f499ab8f3419a15a60b52`
- Route: `VERIFY_LATEST`
- 状态: Enabled, Disabled, Invalid Configuration, Channel Warning, Saving, Validation Error, Channel Unavailable

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 新建/编辑 | DRAWER | `Alert Rule Editor` | UI_ONLY |  |
| 保存 | API | `alert_rule.write` | HIDE_IF_UNSUPPORTED | 按现有Rule schema |
| 启用/停用 | API | `alert_rule.enable_disable` | HIDE_IF_UNSUPPORTED |  |
| 测试通知 | API | `alert_rule.test_notification` | HIDE_IF_UNSUPPORTED |  |
| 删除 | MODAL | `Delete Rule Confirm` | UI_ONLY | 确认后才API |
| 确认删除 | API | `alert_rule.delete` | HIDE_IF_UNSUPPORTED |  |
| 触发记录 | NAVIGATE | `P24?rule=...` | UI_ONLY |  |

## P26 — 审计日志

- Screen ID: `46364c5fee0741ed8e4cd9078bbceac9`
- Route: `VERIFY_LATEST`
- 状态: Loading, Normal, No Result, Error, Partial

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 刷新 | API | `audit.read` | CONFIRMED_CAPABILITY |  |
| 筛选 | API | `audit.read.query` | VERIFY_LATEST |  |
| 审计行 | DRAWER | `Audit Detail` | UI_ONLY |  |
| 复制ID | UI_ONLY | `clipboard.copy` | UI_ONLY | 只读，禁止编辑/删除 |

## P27 — 用户与角色

- Screen ID: `0423092160144335a1941c2f10f895bd`
- Route: `VERIFY_LATEST`
- 状态: Active, Disabled, Saving, Saved, Conflict, Last OWNER Blocked, Loading, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 编辑 | DRAWER | `User Edit` | UI_ONLY |  |
| OWNER风险确认 | MODAL | `OWNER Risk Confirm` | UI_ONLY |  |
| 保存角色/状态 | API | `admin.user.patch` | CONFIRMED_CAPABILITY | 精确route/method VERIFY_LATEST；last-owner以服务端为准 |
| 创建用户 | API | `admin.user.create` | HIDE_IF_UNSUPPORTED |  |

## P28 — 账户与安全

- Screen ID: `ae25511ff98a4b618da646b268092c7c`
- Route: `VERIFY_LATEST`
- 状态: Loading, Password Changing, Password Success, Password Error, Session Active, Session Revoked, Token Active, Token Revoked, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 修改密码 | API | `auth.password_change` | CONFIRMED_CAPABILITY |  |
| 撤销其他会话 | API | `auth.session.revoke` | HIDE_IF_UNSUPPORTED |  |
| 创建API Token | API | `auth.api_token.create` | CONFIRMED_CAPABILITY | 成功打开一次性Secret Modal |
| 复制Token | UI_ONLY | `clipboard.copy` | UI_ONLY |  |
| 我已保存 | UI_ONLY | `close-and-discard-secret` | UI_ONLY | 关闭后不可重新显示 |
| 撤销Token | MODAL | `Revoke Token Confirm` | UI_ONLY |  |
| 确认撤销 | API | `auth.api_token.revoke` | CONFIRMED_CAPABILITY |  |
| 退出登录 | API | `auth.logout/session_end` | CONFIRMED_CAPABILITY | 成功->P01 |

## P29-A — 设置 / 常规

- Screen ID: `42a4488869204a0f8bda07ddef1a8030`
- Route: `VERIFY_LATEST`
- 状态: Saved, Dirty, Saving, Validation Error, Save Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 二级导航 | NAVIGATE | `P29-B/P29-C/P29-D/P29-E` | UI_ONLY |  |
| 保存 | API | `settings.general.write` | HIDE_IF_UNSUPPORTED | 只渲染现有General Settings schema |
| 离开未保存页 | MODAL | `Unsaved Changes` | UI_ONLY | 部署项不可写 |

## P29-B — 设置 / 安全

- Screen ID: `38ceba67ee6043e7b38be362a4f4e868`
- Route: `VERIFY_LATEST`
- 状态: Saved, Dirty, Saving, Validation Error, Conflict, Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 二级导航 | NAVIGATE | `P29-A/P29-C/P29-D/P29-E` | UI_ONLY |  |
| 保存 | API | `settings.security.write` | HIDE_IF_UNSUPPORTED | AUTH_MODE/cookie/keys/trusted proxy/DB只读或隐藏 |
| 离开未保存页 | MODAL | `Unsaved Changes` | UI_ONLY | Stitch示例锁定值不是仓库事实 |

## P29-C — 设置 / 通知

- Screen ID: `a9e40f14556a46a3ad2286f0203955f7`
- Route: `VERIFY_LATEST`
- 状态: Enabled, Disabled, Configured, Not Configured, Testing, Healthy, Failed, Saving, Saved, Validation Error

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 二级导航 | NAVIGATE | `P29-A/P29-B/P29-D/P29-E` | UI_ONLY |  |
| 保存 | API | `settings.notification.write` | HIDE_IF_UNSUPPORTED |  |
| 测试 | API | `notification.channel.test` | HIDE_IF_UNSUPPORTED |  |
| 启用/停用 | API | `notification.channel.enable_disable` | HIDE_IF_UNSUPPORTED | Email/Webhook/Enterprise Messaging具体支持度需复核；Secret不回显 |

## P29-D — 设置 / Integrations

- Screen ID: `f2a7e1bfc752439ea47776acafdc5bbc`
- Route: `VERIFY_LATEST`
- 状态: Configured, Missing Credential, Connected, Failed, Testing, Saving, Saved

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 二级导航 | NAVIGATE | `P29-A/P29-B/P29-C/P29-E` | UI_ONLY |  |
| 保存 | API | `settings.integration.write` | HIDE_IF_UNSUPPORTED |  |
| 测试连接 | API | `integration.connection_test` | HIDE_IF_UNSUPPORTED |  |
| 启用/停用 | API | `integration.enable_disable` | HIDE_IF_UNSUPPORTED | 仅真实存在provider；Secret不回显 |

## P29-E — 设置 / Source Preference

- Screen ID: `0403d8cde45049a39f4a631d5f0405c1`
- Route: `VERIFY_LATEST`
- 状态: Saved, Dirty, Saving, Validation Error, Conflict, Error, Empty

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| 二级导航 | NAVIGATE | `P29-A/P29-B/P29-C/P29-D` | UI_ONLY |  |
| 保存 | API | `source_preference.write` | CONFIRMED_CAPABILITY | 具体schema/route VERIFY_LATEST |
| 恢复默认 | API | `source_preference.restore_default` | HIDE_IF_UNSUPPORTED |  |
| 排序/拖拽 | API | `source_preference.persist_order` | HIDE_IF_UNSUPPORTED |  |

## P30 — 系统诊断

- Screen ID: `bc6128c031404977ae3091932582a9ff`
- Route: `VERIFY_LATEST`
- 状态: Loading, Healthy, Warning, Failed, Unknown, Partial

| 控件 | 动作类型 | 目标/能力 | 绑定 | 实现备注 |
|---|---|---|---|---|
| API Health | API | `GET /health` | CONFIRMED_CAPABILITY | 精确路径已确认 |
| API Readiness | API | `GET /ready` | CONFIRMED_CAPABILITY | 精确路径已确认 |
| 刷新 | API | `diagnostics.read` | VERIFY_LATEST |  |
| 运行记录 | NAVIGATE | `P21` | UI_ONLY |  |
| 来源健康 | NAVIGATE | `P18/P19` | UI_ONLY |  |
| 分析队列 | NAVIGATE | `P23` | UI_ONLY |  |
| 复制ID | UI_ONLY | `clipboard.copy` | UI_ONLY | 严格只读；禁止DB/migration/清队列/重启worker/改环境 |
