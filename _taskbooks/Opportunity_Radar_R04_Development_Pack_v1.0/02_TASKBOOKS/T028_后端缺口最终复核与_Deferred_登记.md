# T028 — 后端缺口最终复核与 Deferred 登记

## 目标

在全部 UI 接线后复核接口缺口，确保不因缺口阻塞产品运行。

## 强制读取顺序

1. `00_START/000_START_PROMPT.md`
2. `01_DEPENDENCIES/000_DESIGN_SYSTEM.md`
3. `04_MANIFESTS/001_UI_DEVELOPMENT_ORDER.csv`
4. `03_REGISTRIES/001_BACKEND_INTERFACE_GAPS.csv`
5. `03_REGISTRIES/003_BACKEND_GAP_POLICY.md`
6. 本任务列出的 UI PNG；然后读取同目录 HTML 了解结构，不把 HTML mock 数据当后端事实。

## UI 依赖

- 无单页视觉依赖；必须读取全局 Manifest / Registry。

## 实施范围

1. 逐项复核 001_BACKEND_INTERFACE_GAPS.csv。
2. 将未满足项定格为 CONTRACT_MISMATCH / CAPABILITY_NOT_EXPOSED / DEFERRED_UNAVAILABLE。
3. 确认每项已有 UI fallback 且不存在假成功。
4. 不得在本任务临时新增后端功能。

## 后端契约处理

- 开工前必须确认本任务所需读取/写入接口是否真实存在、字段和状态语义是否等价。
- 接口不满足时：更新 `03_REGISTRIES/001_BACKEND_INTERFACE_GAPS.csv`，记录证据与 UI fallback。
- 缺口**不得阻塞本任务其余 UI**。
- 未确认写能力只能采用：隐藏、只读、禁用并解释；禁止 fake success。
- 本轮 UI 包不为缺失能力临时制造后端接口；后端修复另立任务。

## 视觉与实现规则

- 当前仓库旧 UI 视觉实现不作为设计依据。
- 可复用现有 API client、types、router/state、tests、tooling，但不得为了迁就旧 UI 改坏 R04 信息架构。
- PNG 是视觉/层级基线；HTML 用于布局结构参考；真实业务数据、字段、枚举、权限以当前仓库后端为准。
- 全部业务文案简体中文；ID、URL、版本、日志、技术字段可保留英文。
- 所有登录后页面复用唯一 AppShell，不允许复制另一套 SideNav/TopBar。
- 不新增无原型依据的 KPI、卡片墙、圆环装饰和后台控制按钮。

## 验收

1. 本任务 UI 与依赖 PNG 在布局、层级、密度和交互语义上等价。
2. 真实接口可用项已接入，不存在硬编码 mock 成功。
3. 接口缺口已登记且有非阻塞 fallback。
4. 相关页面无明显横向溢出、重复元数据、空 Tab、死链接。
5. 相关单元/前端测试通过。
6. `git diff --check` 通过。
7. 暂存内容仅包含本任务预期文件。
8. 更新 `03_REGISTRIES/004_TASK_EXECUTION_LEDGER.csv`。

## Git 提交规则

- 本任务验收 PASS 后执行**一次且仅一次提交**。
- Commit message：`docs(ui): finalize R04 deferred backend gaps`
- 禁止 amend、rebase、squash、force push。
- 本任务不得 push。
- 如果无法证明本任务代码安全完成，结果为 `BLOCKED`，不得生成虚假 PASS 提交。
- 后端接口缺失本身不是 BLOCKED 条件；应登记并继续完成可实现部分。

## 回执格式

`RESULT: PASS` 或 `RESULT: BLOCKED`

并报告：
- Commit SHA
- 修改文件数量
- UI 依赖 ID
- 新增/更新 Backend Gap 数量
- 测试结果
- Working tree 状态
