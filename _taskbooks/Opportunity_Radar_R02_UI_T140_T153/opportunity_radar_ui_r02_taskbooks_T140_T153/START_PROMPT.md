# Opportunity Radar R02 — 总启动指令（T140–T153）

你现在位于 Opportunity Radar 仓库中。目标是依次完成本任务书包的 T140–T153，完成 R02 UI 重构及必要的最小后端接口补充。

## 0. 执行入口

1. 确认当前工作目录是 `D:\github\opportunity-radar` 的仓库根目录；如果实际仓库根目录不同，以当前真实仓库为准。
2. 读取任务书包根目录：
   - `README.md`
   - `RUN_ORDER.md`
   - `dependencies/ui_reference_r02/PROTOTYPE_AUDIT.md`
   - `dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`
   - `dependencies/ui_reference_r02/DESIGN.md`
   - `dependencies/ui_metadata_r02/Opportunity_Radar_R02_UI_Metadata.json`
   - `dependencies/ui_metadata_r02/Opportunity_Radar_R02_Interaction_Flows.md`
3. 然后严格按下面顺序连续执行，不要每个任务都停下来等用户确认：

`T140 → T141 → T142 → T143 → T144 → T145 → T146 → T147 → T148 → T149 → T150 → T151 → T152 → T153`

## 1. 第一原则：先核对 UI 与后端能力

T140 必须是第一项实际工作。在 T140 完成之前，不得开始 R02 视觉页面开发。

对 34 张 UI 的每个按钮、筛选项、保存动作、读取区域、页面跳转逐项核对当前后端：

- 如果后端已有完整能力：绑定真实接口。
- 如果业务能力已经存在，但只是缺 API 暴露、响应字段或轻量接口：**优先补充最小后端接口**，同时补权限、校验、错误处理、审计要求和测试。
- 如果安全补充不了，或者业务能力本身根本不存在：登记为 `DEFERRED_UNAVAILABLE`，明确 UI 是隐藏、只读、禁用说明还是暂不实现，然后继续。
- **接口缺失不得成为后续任务 BLOCKED 的理由。**
- 禁止为了让 UI 看起来完整而新造业务语义、评分逻辑、权限语义、Worker 行为、调度语义、告警语义或审计语义。

## 2. 现有 UI 处理

现有项目的视觉 UI 全部视为废弃。T141 必须清理/退出活动路径。

但是不要机械删除可复用的非视觉代码：

- API client
- domain types
- state/query utilities
- validators
- router infrastructure
- tests
- build/tooling

必须逐项判断是否可复用。禁止把旧页面 CSS/布局复制到 R02。

## 3. 原型使用规则

本任务书包已经清理 Stitch 上传包：

- 保留 34 张 PNG 作为 UI 布局/风格参照；
- 保留 `DESIGN.md`；
- 删除/排除 34 个 `code.html`，因为它们包含 Stitch 生成器的 mock 字段和未验证交互，不可作为实现依据；
- 保留前面生成的 UI metadata / interaction flow 作为查询依赖。

冲突优先级必须是：

`当前仓库真实后端/业务 > T140 解析后的能力矩阵 > 元数据合同 > PNG 布局 > PNG 中的 mock 文案/数值`

## 4. UI 架构顺序

必须先做公共固定区域，再做动态页面：

1. T142：只先构建唯一 AppShell、统一 SideNav、TopBar、全局 Token、PageFrame。
2. T143：构建统一表格、筛选、Badge、Drawer、Modal、状态组件、SettingsFrame 等公共 UI。
3. 后续批次页面必须复用这些公共实现，不允许每个页面自己重新生成导航栏/公共头部。
4. P29A–E 必须是一个固定 SettingsFrame + 五个动态 child frame；切 tab 只刷新 child frame，不能重建 AppShell/Settings 导航。

## 5. 批次开发策略

不要 34 张页面逐页各做一套，也不要一次性全写。按任务书的功能批次开发：

- T144：P01–P05
- T145：P06–P10
- T146：P11–P13
- T147：P14–P17 + P23
- T148：P18–P22
- T149：P24–P25
- T150：P26–P28
- T151：P29A–E + P30

每批结束都必须完成该批真实 API 联调、状态覆盖、交互测试和视觉复核，再进入下一批。

## 6. 普通问题必须自行修复

编译、类型、lint、测试、路由、API client、状态管理、CSS、响应式、测试数据夹具等普通问题必须自行定位并解决，不要因为这些问题停下来。

只有真正的外部阻塞（例如仓库无法读取、必需外部凭据完全不可获得且无法用现有测试方式继续）才允许最终输出 `BLOCKED`。

缺少某个后端 UI 能力不属于 BLOCKED：按 T140 规则补接口或登记后继续。

## 7. Git 规则

- 每个 T140–T153 通过后建立一个独立本地 commit。
- 禁止 amend、rebase、squash、force push。
- **整个序列禁止 push 到远端。**
- T153 最终要求 worktree CLEAN，保留本地 commit 链供用户验收。

## 8. 每个任务回执

每个任务内部完成后可以记录简短回执，但不要停下来询问是否继续。自动进入下一任务。

最终 T153 完成后只输出最终总回执，至少包含：

- `RESULT: PASS` 或真实 `BLOCKED`；
- T140–T153 每任务本地 commit；
- 后端新增/调整接口清单；
- 仍然 `DEFERRED_UNAVAILABLE` 的能力清单及 UI 处理方式；
- 34 张页面实现/验收覆盖情况；
- AppShell/公共组件复用审计；
- frontend/backend 测试与 smoke 结果；
- fake completion 审计；
- 当前 HEAD；
- worktree 是否 CLEAN；
- 明确写出 `REMOTE PUSH: NOT PERFORMED`。

现在开始执行 T140，不要先写 R02 页面。
