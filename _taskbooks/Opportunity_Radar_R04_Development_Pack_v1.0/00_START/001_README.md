# Opportunity Radar R04 Development Pack v1.0

## 包内容

- UI 最终候选：65 个状态，每个状态仅保留 PNG + HTML。
- 开发顺序：U001 → U065。
- 任务书：29 个，T001 → T029。
- 提交规则：每个任务书完成并验收后恰好 1 次 Commit。
- 后端接口缺口：登记、降级、不阻塞其它 UI 和服务运行。
- 最终推送：禁止自动 push，等待人工验收。

## 目录

- `00_START/000_START_PROMPT.md`：总启动指令。
- `01_DEPENDENCIES/000_DESIGN_SYSTEM.md`：统一设计系统。
- `01_DEPENDENCIES/ui/`：按开发顺序编号的 UI PNG + HTML。
- `01_DEPENDENCIES/audit/`：候选审核证据。
- `02_TASKBOOKS/`：29 个任务书。
- `03_REGISTRIES/`：接口缺口、闭环矩阵、执行账本。
- `04_MANIFESTS/`：UI 开发顺序、任务索引、哈希清单。

## 核心冲突优先级

`当前仓库真实后端/业务语义 > T001 实际契约审计 > R04 设计系统 > 选定 PNG > HTML 中的 mock 字段/数值`

## 结果语义

任务回执只使用 `PASS` / `BLOCKED`。
后端能力不存在或契约不匹配，若已有安全 UI fallback，则登记为 Deferred，不得因此把 UI 开发判为 BLOCKED。
