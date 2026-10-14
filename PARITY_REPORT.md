# Opportunity Radar 3.0 全量高保真静态原型验收报告 (PARITY REPORT)

## 一、验收结论

- **总视觉对象目标**：61 / 61
- **主体页面（Main Pages）**：34 / 34（100% 达成）
- **交互状态（State Designs）**：27 / 27（100% 达成）
- **TypeScript 编译**：0 Errors（生产包构建通过）
- **自动化冒烟测试（Smoke Test）**：61 / 61 PASSED（0 错误）
- **1536×1024 视觉比对截图**：61 份对齐截图已归档至 `_evidence/` 目录

---

## 二、核心架构与修正规则执行记录

1. **真实 DOM + SVG 图表实现**：
   - 杜绝使用 PNG 贴图或 CSS 背景充当界面。
   - 所有折线图、环形图、柱状图、网络拓扑图均使用原生 SVG / DOM 渲染，支持悬浮高亮、点击交互与动态数据切换。
2. **AppShell 修正规则严格落地**：
   - `P14 来源管理`：一级导航严格激活高亮为 **「监控」**。
   - `P28-S01 外部集成授权与修复`：采用 **P28 父页面 + 右侧 Drawer** 实现，保持 AppShell 完整上下文。
   - `P31-S01 全局搜索无结果`：采用 **P31 父页面 AppShell**，只替换主体结果区域为高保真空状态。
   - `P32 登录`：采用独立双栏 `AUTH_SHELL`，左侧科技背景，右侧登录表单与 MFA 验证。
   - `P33 403 / P34 404`：采用 `MINIMAL_APP_SHELL`。
3. **数据链闭环与固定 Mock 实体**：
   - 跨页面一致性 ID：`OPP-20260819-021`、`INT-20260819-01842`、`PLAN-2025-001`、`RUN-20260819-1048`、`AL-20260819-01528`、`RES-20260819-0011`。

---

## 三、各模块快速访问清单 (127.0.0.1:3000)

| 模块 | 页面名称 | 访问路由 | 状态参数示例 |
|---|---|---|---|
| **今日雷达** | 今日雷达 | `http://localhost:3000/today` | - |
| **情报发现** | 情报列表 | `http://localhost:3000/intelligence` | - |
| | 情报详情 | `http://localhost:3000/intelligence/INT-20260819-01842` | `?state=P03-S01` (创建机会抽屉) |
| | 关键词发现 | `http://localhost:3000/keywords/discovery` | - |
| | 关注关键词 | `http://localhost:3000/keywords/tracked` | - |
| | 趋势分析 | `http://localhost:3000/trends` | - |
| **机会研判** | 关系图谱 | `http://localhost:3000/graph` | - |
| | 机会池 | `http://localhost:3000/opportunities` | - |
| | 机会详情 | `http://localhost:3000/opportunities/OPP-20260819-021` | `?state=P09-S01` (修改状态) |
| | 结构化分析 | `http://localhost:3000/opportunities/OPP-20260819-021/analysis` | `?state=P09-S04` |
| **研究闭环** | 研究工作流 | `http://localhost:3000/research` | `?state=P11-S01` (新建研究) |
| | 研究工作流详情 | `http://localhost:3000/research/RES-20260819-0011` | `?state=P12-S01` (步骤异常) |
| | 研究结论 | `http://localhost:3000/research/RES-20260819-0011/result` | `?state=P13-S01` (发布结论) |
| **监控与来源** | 来源管理 | `http://localhost:3000/sources` | - |
| | 来源详情 | `http://localhost:3000/sources/reuters` | - |
| | 来源健康 | `http://localhost:3000/sources/health` | - |
| | 监控计划 | `http://localhost:3000/monitoring` | `?state=P17-S01` (新建计划) |
| | 监控计划详情 | `http://localhost:3000/monitoring/PLAN-2025-001` | `?state=P17-S03` (手动运行) |
| | 运行记录 | `http://localhost:3000/runs` | - |
| | 运行详情 | `http://localhost:3000/runs/RUN-20260819-1048` | `?state=P20-S01` (错误详情) |
| | 分析队列 | `http://localhost:3000/analysis-queue` | `?state=P21-S01` |
| | 告警中心 | `http://localhost:3000/alerts` | `?state=P22-S01` (处理告警) |
| | 告警规则 | `http://localhost:3000/alert-rules` | `?state=P23-S01` (新建规则) |
| **设置与治理** | 工作区设置 | `http://localhost:3000/settings/workspace` | - |
| | 成员管理 | `http://localhost:3000/settings/members` | `?state=P25-S01` (邀请成员) |
| | 角色与权限 | `http://localhost:3000/settings/roles` | `?state=P26-S01` (编辑权限) |
| | 账户安全 | `http://localhost:3000/settings/security` | `?state=P27-S01` (开通MFA) |
| | 外部集成 | `http://localhost:3000/settings/integrations` | `?state=P28-S01` (修复集成抽屉) |
| | 审计日志 | `http://localhost:3000/settings/audit` | - |
| | 系统诊断 | `http://localhost:3000/settings/diagnostics` | - |
| **全局与系统** | 全局搜索 | `http://localhost:3000/search` | `?state=P31-S01` (无结果空状态) |
| | 登录 | `http://localhost:3000/login` | `?state=P32-S01` (MFA二次验证) |
| | 403 无权限 | `http://localhost:3000/access-denied` | `?state=P33-S01` (申请权限) |
| | 404 页面未找到 | `http://localhost:3000/404` | - |
