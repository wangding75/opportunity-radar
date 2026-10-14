# Opportunity Radar R04 — 总启动指令

你现在负责在 `D:\github\opportunity-radar` 中实施 Opportunity Radar R04 中文业务闭环 UI。

本轮目标不是继续设计页面，而是严格按已审核的 65 个最终 UI 状态进行代码重建、真实接口接线、闭环验收和分任务提交。

## A. 从解压开始

1. 仓库固定为 `D:\github\opportunity-radar`。
2. 在用户 Downloads 目录查找 `Opportunity_Radar_R04_Development_Pack_v1.0.zip`。
3. 将其解压到仓库的 `_taskbooks\Opportunity_Radar_R04_Development_Pack_v1.0`。
4. 校验压缩包/解压文件完整性，读取 `04_MANIFESTS/999_SHA256SUMS.txt`。
5. 若同名目录已存在，不得直接覆盖；先确认内容哈希，内容一致则复用，不一致则 BLOCKED 并报告。
6. 不要修改压缩包内原始 UI 依赖文件；实现代码写入项目正式源码目录。

## B. 启动前必须读取

按以下顺序读取：

1. `00_START/001_README.md`
2. `01_DEPENDENCIES/000_DESIGN_SYSTEM.md`
3. `01_DEPENDENCIES/audit/001_UI_AUDIT_RESULT.md`
4. `04_MANIFESTS/001_UI_DEVELOPMENT_ORDER.csv`
5. `04_MANIFESTS/002_TASKBOOK_INDEX.csv`
6. `03_REGISTRIES/001_BACKEND_INTERFACE_GAPS.csv`
7. `03_REGISTRIES/002_UI_CLOSED_LOOP_MATRIX.csv`
8. `03_REGISTRIES/003_BACKEND_GAP_POLICY.md`
9. T001 任务书

## C. 总执行原则

1. 严格按 `T001 → T029` 顺序执行，不跳任务，不并行制造相互覆盖的 UI。
2. 每个任务书开始前先读取该任务列出的 UI PNG，再读取同目录 HTML。
3. PNG 是视觉、信息层级与页面状态基线；HTML 只用于辅助理解结构和组件。
4. HTML 中的 mock 文案、数字、状态、字段不得当成后端事实。
5. 业务事实和数据契约优先级：当前仓库真实后端/业务语义 > T001 契约审计 > R04 设计系统 > PNG > HTML mock。
6. 现有旧 UI 视觉实现全部视为废弃，不得继续修修补补形成两套设计。
7. 可以复用旧项目中不带视觉偏差的 API client、types、router/state、tests、tooling。
8. 必须先完成唯一 AppShell，再开发业务页；任何业务页不得复制另一套导航栏、顶栏或公共头部。
9. 所有用户可见业务文案使用简体中文；ID、URL、版本号、技术日志可保留英文。
10. 禁止将页面做成 KPI 卡片墙、BI 大屏、圆环装饰页；禁止重复展示同一实体元数据。

## D. 后端接口缺口规则

1. T001 必须先对 UI 所需能力与真实后端逐项核对。
2. 后续每个任务在接线前继续做局部契约复核。
3. 后端接口满足且语义等价：接真实接口，登记 `MATCHED`。
4. 字段/状态/权限语义不等价：登记 `CONTRACT_MISMATCH`。
5. 后端内部有能力但没有安全 API 暴露：登记 `CAPABILITY_NOT_EXPOSED`。
6. 能力不存在：登记 `DEFERRED_UNAVAILABLE`。
7. 所有缺口写入 `03_REGISTRIES/001_BACKEND_INTERFACE_GAPS.csv`，必须包含证据和 UI fallback。
8. 后端接口缺失**不得阻塞其它 UI、Docker 启动、读取链或浏览器验收**。
9. 缺口页面采用隐藏、只读或禁用并解释的方式降级。
10. 严禁 fake success：不能本地改状态后提示“保存成功”，不能假装后端已经执行。
11. 本任务包以 R04 UI 重建为目标；缺失后端能力不在本轮临时补造，统一登记后另立后端修复任务。

## E. Git 规则

1. 开始 T001 前记录当前 branch、HEAD、working tree。
2. 每个任务书必须独立完成、独立测试、独立验收。
3. 每个任务书 PASS 后执行一次且仅一次 Commit。
4. Commit message 使用任务书指定内容。
5. 禁止 amend、rebase、squash、force push。
6. 禁止把多个任务书合并成一个 Commit。
7. BLOCKED 的任务不得生成虚假完成 Commit。
8. 本轮全部任务都禁止 push；等待用户最终 Review 后再决定推送。
9. 每个任务完成后暂存区必须为空，工作区只能存在明确允许的下一任务输入或执行记录。

## F. UI 依赖读取规则

1. UI 文件已经按开发顺序编号：`U001 → U065`。
2. 每个 UI 目录只包含对应 `Uxxx_screen.png` 与 `Uxxx_code.html`。
3. 任务书中的 UI 依赖 ID 必须通过 `04_MANIFESTS/001_UI_DEVELOPMENT_ORDER.csv` 解析到具体文件。
4. 不允许用已淘汰候选替换最终候选。
5. `U001 S00_AppShell_Master` 只作为外壳/组件基准，不是业务路由；其示例性按钮和数据不得据此实现业务能力。
6. 对有 `SELECTED_WITH_GEOMETRY_WARNING` 的页面，保留其信息架构和内容，但实现时必须回到统一 AppShell 固定视口与内容区内部滚动。

## G. 闭环 Gate

T026 必须逐条执行 `03_REGISTRIES/002_UI_CLOSED_LOOP_MATRIX.csv`，至少覆盖：

- 工作台 → 机会 → 详情 → 证据 → 情报/来源 → 研究 → 返回机会
- 情报 → 原始证据/关系/处理过程 → 数据源/运行/队列
- 研究列表 → 任务/分析/结果详情 → 证据 → 来源/机会
- 监控计划 → 数据源 → 运行 → 日志/产出/关联对象
- 告警 → 运行/来源/机会
- 用户/设置 → 审计/诊断
- 全局搜索、通知、帮助、头像、登录帮助、403、404

验收时不得存在：空 Tab、死链接、固定对象 ID 跳转、跨对象串数据、伪写按钮、无返回路径。

## H. 运行与验收

1. 整个服务最终必须按项目 Docker build/run 方式启动和验收。
2. 不使用“本地能打开静态 HTML”替代真实服务验收。
3. 运行现有 Python、前端、lint/静态检查、产品 smoke；不得减少原有测试覆盖。
4. T027 做多视口浏览器视觉验收，重点检查 AppShell 一致性、中文、密度、滚动、横向溢出和重复信息。
5. T029 做最终 Docker 联调和 65 个 UI 状态的浏览器验收。
6. 后端 Deferred 项只要有明确安全 fallback 且不影响其它链路，不作为最终运行 BLOCKER。

## I. 每任务回执

每完成一个任务只回执：

`RESULT: PASS` 或 `RESULT: BLOCKED`

同时报告：

- Task ID
- Commit SHA
- 修改文件数
- UI 依赖 ID
- Backend Gap 新增/更新数量
- 测试结果
- Docker/浏览器状态（适用时）
- staged 状态
- working tree 状态
- 是否 push（必须为 NONE）

PASS 后自动进入下一任务，直到 T029。除非真正 BLOCKED，不要停下来等待人工逐任务确认。

## J. 现在开始

从解压和哈希校验开始，然后执行 T001。不要跳过契约审计，不要先写业务页面，不要先修改后端，不要 push。
