# React 产品化优化主执行计划

日期：2026-09-04  
状态：执行中（PLAN-03 / PLAN-04 样板页视觉收口）  
适用范围：根目录 React 原型、FastAPI 后端、生产发布链路  
关联文档：

- [`REACT_PROTOTYPE_GLOBAL_REVIEW.md`](REACT_PROTOTYPE_GLOBAL_REVIEW.md)
- [`REACT_VISUAL_REDESIGN_SPEC.md`](REACT_VISUAL_REDESIGN_SPEC.md)
- [`REACT_PROTOTYPE_BACKEND_DEVELOPMENT_PLAN.md`](REACT_PROTOTYPE_BACKEND_DEVELOPMENT_PLAN.md)

## 1. 总体目标

把当前 34 页、27 个状态的静态 React 原型升级为真实可发布产品，同时完成：

1. 重构整体布局、视觉层级和公共组件，不以简单放大字体代替设计优化。
2. 建立 API、鉴权、RBAC、错误、异步任务和公共 ID 等前端基础能力。
3. 复用现有 FastAPI 能力，并按业务价值补齐缺失的后端领域模型和接口。
4. 移除生产 mock 和假成功交互，让每个用户动作都能回读、失败、重试和审计。
5. 建立响应式、可访问性、视觉回归、契约、安全、性能和发布门禁。

计划使用依赖顺序而非日历估时。实际周期取决于团队人数、后端优先级和是否同时交付 MFA、SSO、自定义角色等高风险能力。

## 2. 计划总览

| 计划 | 名称 | 目标 | 依赖 | 完成门 |
|---|---|---|---|---|
| PLAN-00 | 基线与治理 | 冻结范围、建立任务和验收基线 | 无 | 页面/能力/测试基线可追踪 |
| PLAN-01 | 视觉系统重构 | 确立整体美化标准和页面模板 | PLAN-00 | Token、模板和视觉样板评审通过 |
| PLAN-02 | React 产品基础 | API、Auth、Router、状态、生产构建 | PLAN-00 | React 可作为安全生产入口 |
| PLAN-03 | AppShell 与公共组件 | 建立全站统一布局和组件 | PLAN-01、02 | 公共组件满足响应式和 AA |
| PLAN-04 | 五个样板页 | 验证五类核心页面设计 | PLAN-03 | P01/P02/P09/P24/P32 视觉签收 |
| PLAN-05 | 情报与机会闭环 | 打通 P01–P10 数据与操作 | PLAN-02、04 | 核心发现→研判闭环无 mock |
| PLAN-06 | 研究闭环 | 新增研究领域并打通 P11–P13 | PLAN-05 | 研究流程可执行、发布、追溯 |
| PLAN-07 | 来源与运行闭环 | 打通 P14–P21 | PLAN-05 | 来源→计划→运行→诊断闭环 |
| PLAN-08 | 告警与治理闭环 | 打通 P22–P34 | PLAN-05；部分依赖 06/07 | 告警、管理、安全、搜索可用 |
| PLAN-09 | 全局 QA 与发布 | 性能、安全、迁移、灰度、回滚 | PLAN-05–08 | 全部门禁通过并切换默认入口 |

依赖关系：

```text
PLAN-00 ─┬─> PLAN-01 ─┐
         └─> PLAN-02 ─┴─> PLAN-03 ─> PLAN-04 ─> PLAN-05
                                                    ├─> PLAN-06 ─┐
                                                    ├─> PLAN-07 ─┼─> PLAN-08 ─> PLAN-09
                                                    └────────────┘
```

## 3. PLAN-00：基线与治理

目标：让后续每个任务都可以判断范围、完成度和回归影响。

### BASE-001：冻结 React 原型为产品 UI 基准

**状态：已完成（2026-09-04）**。交付见 [`REACT_PRODUCT_BASELINE.md`](REACT_PRODUCT_BASELINE.md)。

- **实施内容**：记录根 `src/`、34 页面路由、27 状态、关键业务对象和当前截图；明确旧 `frontend/` 仅作 API 参考。
- **交付物**：页面清单、状态清单、基准截图索引、基准 commit SHA。
- **依赖**：无。
- **验收**：任何页面或状态都能通过稳定 ID 定位；团队不会继续在两套前端上并行开发。

### BASE-002：建立页面—能力—接口追踪矩阵

**状态：已完成（2026-09-04）**。交付见 [`REACT_PAGE_CAPABILITY_MATRIX.md`](REACT_PAGE_CAPABILITY_MATRIX.md)。

- **实施内容**：以 P01–P34 为行，登记读/写动作、当前 API、目标 API、权限、状态、后端任务和 UI fallback。
- **交付物**：可更新矩阵；初始内容来自后端开发计划第 3 节。
- **依赖**：BASE-001。
- **验收**：每个可见按钮都被分类为真实接口、UI-only、隐藏、只读或待开发；不存在未登记成功动作。

### BASE-003：建立测试与指标基线

**状态：已完成（2026-09-04）**。根 React 构建已加入 CI，五视口采集脚本为 `npm run test:ui-baseline`；基线说明见 [`REACT_PRODUCT_BASELINE.md`](REACT_PRODUCT_BASELINE.md)。

- **实施内容**：保留当前 `tsc`、61 路由 smoke、379 个后端测试；记录五档视口截图、横向溢出、最小字号、关键页面性能和 bundle 基线。
- **交付物**：baseline report、CI job 清单。
- **依赖**：BASE-001。
- **验收**：后续 PR 能自动比较类型、单测、视觉、响应式、可访问性和 bundle 变化。

### BASE-004：制定变更与评审规则

**状态：已完成（2026-09-04）**。交付见 [`REACT_CHANGE_REVIEW_CHECKLIST.md`](REACT_CHANGE_REVIEW_CHECKLIST.md)。

- **实施内容**：一个任务只处理一个明确契约；数据库迁移、OpenAPI、前端类型、UI 状态和测试随功能一起提交；禁止先合并假按钮。
- **交付物**：PR checklist、Definition of Done。
- **依赖**：BASE-002、003。
- **验收**：PR 模板要求提供截图、接口差异、权限、失败态和回滚说明。

## 4. PLAN-01：视觉系统重构

目标：把“统一小卡片后台”重构为具有主次、节奏与可信感的情报产品。

### VIS-001：确定视觉方向与语义原则

**状态：已完成（2026-09-04）**。视觉原则、页面模板和 do/don't 见 [`REACT_VISUAL_REDESIGN_SPEC.md`](REACT_VISUAL_REDESIGN_SPEC.md)。

- **实施内容**：采用 Calm Intelligence / Evidence First / Actionable；确定每屏一个视觉重心、一个主动作、语义色不装饰化等原则。
- **交付物**：视觉原则页、do/don't 示例。
- **依赖**：BASE-001。
- **验收**：设计、产品和前端能用同一原则判断一个页面是否过度卡片化或缺少重点。

### VIS-002：重建 Design Tokens

**状态：执行中（2026-09-04）**。已完成全局 token、视口和最小字号基线改造；逐页清理硬编码样式与模板接入将在 VIS-003–004 完成。

- **实施内容**：重建 typography、line-height、spacing、color、surface、border、radius、shadow、z-index、motion 和 breakpoint token；清理 10px/11px 交互文字。
- **交付物**：新的 token 文件和 token 文档。
- **依赖**：VIS-001。
- **验收**：页面不得直接声明新的颜色、阴影、圆角和字号；交互文字不低于 14px；辅助文字满足对比度。

### VIS-003：建立六类页面模板

**状态：已完成（2026-09-04）**。组件位于 `src/layouts/PageTemplates.tsx`，34 页归属见 [`REACT_LAYOUT_TEMPLATE_MANIFEST.md`](REACT_LAYOUT_TEMPLATE_MANIFEST.md)；样板页将在 PLAN-04 接入并验收。

- **实施内容**：实现分诊工作台、列表工作台、实体详情、分析画布、设置治理、认证/系统状态六类栅格和响应式规则。
- **交付物**：Layout components、模板 Storybook/开发路由或等价展示页。
- **依赖**：VIS-002。
- **验收**：34 页均能归入一种模板；不再逐页创建任意 grid。

### VIS-004：定义 Surface 与视觉层级

**状态：已完成（2026-09-04）**。`Surface`、`Section`、`InsightBanner`、`ActionPanel` 位于 `src/components/common/Surface.tsx`；样板页会在 PLAN-04 使用这些 primitives。

- **实施内容**：限定 Page/Surface/Raised 三层表面；减少边框和嵌套卡片；建立标题、结论条、行动面板、证据块的视觉区别。
- **交付物**：Surface、Section、InsightBanner、ActionPanel 规范。
- **依赖**：VIS-002。
- **验收**：同页最多三种 surface；卡片嵌套不超过一层；纯分组优先标题、留白和 divider。

### VIS-005：定义数据可视化语言

**状态：已完成（2026-09-04）**。规范见 [`REACT_DATA_VISUALIZATION_SPEC.md`](REACT_DATA_VISUALIZATION_SPEC.md)，公共容器为 `ChartFrame`；现有折线图的坐标和主/异常序列已切换到语义 token，字体不低于 12px。

- **实施内容**：统一主序列、对比序列、异常点、网格、坐标、tooltip、单位和数据表替代视图；移除装饰性图表。
- **交付物**：Line/Bar/Donut/Trend/Graph 规范和示例。
- **依赖**：VIS-002。
- **验收**：图表文字不低于 12px；颜色不超过五个系列；每张图有结论、时间窗、口径和来源。

### VIS-006：视觉内容与文案规范

**状态：已完成（2026-09-04）**。交付见 [`REACT_UI_COPY_GLOSSARY.md`](REACT_UI_COPY_GLOSSARY.md)。

- **实施内容**：规定页面标题、副标题、结论句、状态、按钮、空态和错误文案；统一“任务已创建”与“业务已完成”。
- **交付物**：UI copy glossary。
- **依赖**：VIS-001。
- **验收**：页面没有重复标题、技术占位词和虚假成功文案；关键数字说明单位和时间窗。

## 5. PLAN-02：React 产品基础

目标：让 React 具备真实应用需要的数据、权限、路由和发布能力。

### FE-001：重组前端目录与模块边界

**状态：已完成（2026-09-04）**。已建立 `app/api/features/components/layouts/mock` 边界说明、`@/*` 别名和增量迁移规则；现有原型页会在对应业务包接入时逐页迁移，避免一次性移动 34 页。

- **实施内容**：建立 `app/api/features/components/layouts/mocks` 边界；把业务页、设计系统和数据访问拆开；设置绝对 import。
- **交付物**：新目录结构、依赖规则、迁移说明。
- **依赖**：BASE-004。
- **验收**：页面组件不直接拼请求、权限、toast 和大段样式；feature 之间无循环依赖。

### FE-002：建立类型安全 API Client

**状态：执行中（2026-09-04）**。统一 client、请求 ID、CSRF、取消、下载和 FastAPI 兼容错误归一化已建立于 `src/api/`；待 BE-00 锁定错误 envelope/OpenAPI 后生成完整类型并接入 feature。

- **实施内容**：基于 OpenAPI 生成类型；封装 cookie、CSRF、request ID、错误 envelope、取消请求、文件下载和 429；禁止页面直接 `fetch`。
- **交付物**：API client、generated types、contract tests。
- **依赖**：FE-001；后端错误契约可先锁定。
- **验收**：所有请求从统一 client 发出；401/403/409/422/429/5xx 有标准化结果；日志不输出凭据。

### FE-003：建立 Auth 与 RBAC

**状态：执行中（2026-09-04）**。已建立 AuthProvider 与 PermissionGate；通过 `VITE_ENABLE_API=true` 启用现有登录 bootstrap。路由保护与页面级权限收敛待正式路由和 feature 数据接入后启用，避免把原型导航误判为生产鉴权。

- **实施内容**：AuthProvider、登录 bootstrap、受保护路由、PermissionGate、会话过期、登出和 CSRF；角色仍由服务端最终裁决。
- **交付物**：auth store/hooks、route guard、permission component。
- **依赖**：FE-002。
- **验收**：未登录不能打开业务页；VIEWER 看不到写动作；403 有可恢复上下文；刷新不丢会话。

### FE-004：重建 Router 与公共 ID 参数

**状态：执行中（2026-09-04）**。34 页已改为路由级 lazy load；`RouterContext` 已暴露统一实体参数解析。最终 public ID 格式、正式路由库替换和详情服务端回读依赖 BE-00/BE-01/BE-02 的契约落地。

- **实施内容**：使用正式路由库或等价稳定实现；解析 entity public ID、search params、404、back/forward、unsaved form guard；实现路由级 lazy load。
- **交付物**：typed route definitions、entity parameter hooks。
- **依赖**：FE-001、后端 public ID 决策。
- **验收**：不同详情 URL 显示不同实体；直接刷新和返回键正确；不存在固定读取 mock 首项。

### FE-005：建立 Query、Form 与错误状态

**状态：执行中（2026-09-04）**。`useAsyncResource` 处理取消和陈旧数据，`AsyncState` 提供 loading/empty/error/partial 基元。待正式 feature 接口接入后补 query cache、mutation/form adapter 与竞态测试。

- **实施内容**：统一 server state cache、loading/empty/error/partial/stale/retry、mutation pending、表单校验和 dirty state。
- **交付物**：query provider、error boundary、form adapters、状态组件。
- **依赖**：FE-002。
- **验收**：请求竞态不会覆盖新数据；写失败不显示成功；刷新后以服务端回读为准。

### FE-006：隔离 Mock 与防假成功门禁

**状态：执行中（2026-09-04）**。已完成 mock/假成功登记（[`REACT_MOCK_TRANSITION_REGISTER.md`](REACT_MOCK_TRANSITION_REGISTER.md)）；生产禁止规则必须随每个对应 BE 契约和页面迁移一起启用，不能在仍有 9 个 mock 页面时伪造通过。

- **实施内容**：mock 仅在 dev/test fixture 使用；production build 增加禁止 `src/mock` import 的检查；未接接口按钮隐藏、只读或明确禁用。
- **交付物**：mock adapter、production scan、fake-success test。
- **依赖**：FE-001、005。
- **验收**：生产 bundle 没有 mock 业务记录；所有成功 toast 都能追踪到成功 mutation 或纯 UI 行为。

### FE-007：React 生产构建与 SPA 发布

**状态：执行中（2026-09-04）**。Docker 已加入 React 多阶段构建，FastAPI 支持 `UI_MODE=react` 时的 hashed assets 与 deep-link fallback；默认 `UI_MODE=legacy` 保持现有入口可回滚。只有 mock 清零、真实 Auth/API 接入和发布验收完成后，才允许将生产默认值切换为 `react`。

- **实施内容**：Docker 多阶段构建；FastAPI/Caddy 发布 hashed assets；实现 deep-link fallback；自托管字体；更新 CSP/cache/source map。
- **交付物**：Dockerfile/compose/Caddy/FastAPI 静态入口变更和部署测试。
- **依赖**：FE-001；可与 FE-002–006 并行。
- **验收**：所有 React 路由直接访问/刷新成功；旧 UI 不再是默认入口；CSP console 无错误；可回滚旧入口。

## 6. PLAN-03：AppShell 与公共组件

目标：通过公共组件一次解决布局、美感、响应式和可访问性问题。

### UI-001：重做 AppShell

**状态：执行中（2026-09-04）**。已交付响应式 AppShell、桌面侧栏/顶栏和移动端抽屉导航；P01/P02/P09/P24/P32 的五档视口无文档级横向溢出。其余 29 页和全局键盘/通知语义仍待随批量迁移验证。

- **实施内容**：208–216px/64px 侧栏、64px 顶栏、1440px 工作区、统一 gutter；实现桌面/平板/移动导航状态。
- **交付物**：AppShell、SidebarNav、TopBar、MobileNav。
- **依赖**：VIS-002、003；FE-003、004。
- **验收**：390/768/1024/1280/1536 无文档级横向滚动；active module、通知、账户和搜索语义正确。

### UI-002：实现 PageHeader 与 EntityHeader

**状态：执行中（2026-09-04）**。`PageHeader` 已支持小屏标题、摘要和操作区重排，样板页标题不再与操作挤压；详情实体头和动作 overflow 仍需按正式数据契约收敛。

- **实施内容**：统一 breadcrumb、标题、副标题、状态、元数据、更新时间和操作折叠；每屏最多一个 primary action。
- **交付物**：PageHeader、EntityHeader、ActionOverflow。
- **依赖**：VIS-003、004。
- **验收**：页面没有重复 header；详情关键元数据不在正文重复；窄屏操作进入 overflow。

### UI-003：重做按钮、表单和标签

**状态：执行中（2026-09-04）**。全局字号与控制高度 token 已上调，样板页中不可用的后端动作明确标为“待接入”并禁用；基础组件变体、加载态和完整焦点审计尚未完成。

- **实施内容**：Button/IconButton/Input/Select/Textarea/Switch/Checkbox/Badge/Tag；补齐 hover/focus/disabled/loading/error。
- **交付物**：表单基础组件与使用规范。
- **依赖**：VIS-002。
- **验收**：控件字号至少 14px；常规高度至少 36/40px；icon button 有可访问名称；无 `outline:none` 裸状态。

### UI-004：重做 FilterBar、Table 和 Pagination

- **实施内容**：saved view、常用/高级筛选、列优先级、排序、选择、批量动作、cursor pagination、窄屏卡片形态。
- **交付物**：DataTable family、FilterBar、Pagination。
- **依赖**：UI-003；FE-005。
- **验收**：1280px 标题列不逐字换行；390px 有可读替代布局；键盘可选择和进入详情。

### UI-005：重做 Card、Metric、状态与反馈组件

**状态：执行中（2026-09-04）**。`Surface`、`Section`、`InsightBanner`、`ActionPanel`、`AsyncState` 和 `ChartFrame` 已落地并用于样板页；真实请求的 loading/empty/error/partial 接入待领域接口完成。

- **实施内容**：减少通用 Card 滥用；实现 MetricGroup、InsightBanner、ActionPanel、Skeleton、Empty、Error、Partial、Stale、Toast。
- **交付物**：反馈组件库。
- **依赖**：VIS-004、006；FE-005。
- **验收**：loading skeleton 与最终布局一致；错误包含 request ID；异步 job 不用短暂 toast 冒充完成。

### UI-006：重做 Drawer、Modal、Tabs

- **实施内容**：dialog semantics、focus trap/return、Esc、scroll lock、标题关联、pending close guard；Tabs 支持键盘方向键。
- **交付物**：Overlay primitives、Tabs。
- **依赖**：UI-003。
- **验收**：键盘和屏幕阅读器完整可用；关闭后焦点返回触发点；长表单使用 Drawer 而非窄 Modal。

### UI-007：重做 Charts 与 Graph 容器

**状态：执行中（2026-09-04）**。图表容器和语义色、12px 最小坐标字号已落地；tooltip、数据表替代和关系图交互仍待接入真实数据。

- **实施内容**：实现图表 theme、tooltip、legend、resize observer、空态、数据表替代；关系图支持 zoom/pan/focus。
- **交付物**：ChartFrame、TrendChart、DistributionChart、GraphCanvas。
- **依赖**：VIS-005；UI-003。
- **验收**：容器缩放不裁切；坐标不小于 12px；异常不只靠颜色；可读取原始数据。

### UI-008：公共组件可访问性门禁

- **实施内容**：axe、keyboard、focus、200% zoom、contrast 和 reduced-motion 测试。
- **交付物**：组件级 a11y suite。
- **依赖**：UI-001–007。
- **验收**：公共组件无 critical/serious axe 问题；所有动作只用键盘可以完成。

## 7. PLAN-04：五个样板页

目标：先验证视觉与工程方案，再批量迁移 34 页。

### SAMPLE-001：P01 今日雷达

**状态：视觉实现完成，业务接入待 PLAN-05（2026-09-04）**。今日结论、优先机会、行动项和紧凑指标已重构；五档视口无横向溢出，真实 dashboard 聚合和行动写入尚未接入。

- **实施内容**：六 KPI 卡改为今日简报 + 3–4 个紧凑指标；建立 8/4 优先信息与待办结构；合并异常和可信度。
- **交付物**：新 P01、五档截图、数据状态 Story/fixture。
- **依赖**：UI-001、002、005、007。
- **验收**：5 秒内可识别今日主结论、最高风险和下一步；不再是 12 张同权卡片。

### SAMPLE-002：P02 情报列表

**状态：部分完成（2026-09-04）**。宽屏采用列表/预览分栏，窄屏改为可读卡片；`VITE_ENABLE_API=true` 时已接入真实 Observation 列表、公共 ID、来源/对象类型/时间窗筛选及 loading/empty/error。订阅、收藏、人工创建和全页详情仍保持禁用或 mock，直至对应契约落地。

- **实施内容**：重排搜索/筛选/saved view；>=1440 使用 8/4 预览；<1440 使用 Drawer；设定列宽和截断。
- **交付物**：新 P02、Table/preview 实战验证。
- **依赖**：UI-002、004、006。
- **验收**：1280px 表格可扫描；390px 使用卡片或优先列；预览不挤压主列表。

### SAMPLE-003：P09 机会详情

**状态：部分完成（2026-09-04）**。主列改为证据与判断、侧栏改为行动面板；`VITE_ENABLE_API=true` 时使用 opportunity `public_id` 读取真实评分、关键词、分析摘要、研究摘要和证据。状态、负责人、结构化分析和备注写入仍禁用，且分析/图谱/趋势子页尚待对应领域接口接入。

- **实施内容**：EntityHeader 合并状态/评分/负责人；一个主动作；证据时间线为主列，行动面板为侧栏；消除重复 KPI。
- **交付物**：新 P09、详情模板验证。
- **依赖**：UI-002、005、006、007。
- **验收**：用户能先理解机会判断，再看证据，再采取行动；状态和评分不重复出现。

### SAMPLE-004：P24 工作区设置

**状态：视觉实现完成，业务接入待 PLAN-08（2026-09-04）**。设置导航与单内容列已重构，危险操作与保存保持受控禁用，等待工作区资源与审计契约。

- **实施内容**：224px 二级导航 + 单内容列；按路由拆主题；重新分类数据管理/保留/配置/危险操作；dirty save bar。
- **交付物**：新 P24、SettingsLayout。
- **依赖**：UI-001–003、005、006。
- **验收**：页面不再是设置卡片墙；只有删除进入危险区；无变更时不显示保存。

### SAMPLE-005：P32 登录

**状态：部分完成（2026-09-04）**。桌面/移动布局已重构，390px 无横向溢出；`VITE_ENABLE_API=true` 时密码登录调用真实会话接口。MFA、SSO、找回密码及 401/429/不可用的真实端到端验收仍待认证契约完善。

- **实施内容**：调整 45/55 比例、表单宽度和品牌文案；接真实密码登录状态；MFA/SSO 未完成时不伪造。
- **交付物**：新 P32、AuthLayout。
- **依赖**：UI-003、005；FE-003。
- **验收**：登录、401、429、服务不可用、会话恢复均真实；窄屏切换为单栏。

### SAMPLE-006：样板评审门

**状态：待执行**。视觉样板的构建与 25 组断点检查已通过，但该评审门还需要真实数据长度、异常状态和 API fallback 的联调证据。

- **实施内容**：产品、设计、前端、后端共同检查视觉原则、真实数据长度、状态、API fallback 和响应式。
- **交付物**：签收记录和必须修改清单。
- **依赖**：SAMPLE-001–005。
- **验收**：五页全部通过视觉验收清单；公共规则冻结后才能批量迁移。

## 8. PLAN-05：情报与机会闭环（P01–P10）

目标：完成“发现信号→查看证据→关注关键词→趋势/关系→形成机会→结构化分析”。

### CORE-001：公共 ID 与 Bootstrap 后端契约

**状态：部分完成（2026-09-04）**。`GET /api/v1/auth/bootstrap` 已返回 session、单工作区摘要、模块、feature flag 和服务端时间；错误响应已提供 `code/message/field_errors/request_id/retryable`，并为旧调用方暂留 `detail`。Opportunity 已输出并接受 `public_id`，其余领域实体、OpenAPI 类型生成和 React feature 的真实数据接入待后续任务完成。

- **实施内容**：为主要实体确定 public ID；新增 bootstrap；统一 error envelope；保留兼容读取。
- **交付物**：模型迁移、OpenAPI、兼容策略、后端测试。
- **依赖**：BASE-002；FE-002、004 可使用草案并行。
- **验收**：产品 URL 不使用数据库自增 ID；bootstrap 返回当前用户、权限、feature flags 和服务时间。

### CORE-002：情报详情与用户状态

**状态：部分完成（2026-09-04）**。Observation 列表与详情已能以稳定公共 ID 读取，详情主动排除原始 payload；书签、忽略、备注、订阅、人工创建与证据来源标注仍待 `UserObservationState` 等模型和权限规则落地。

- **实施内容**：Observation detail、bookmark、dismiss、subscription、人工创建边界、实体/关键词/关联对象；记录用户状态和证据来源。
- **交付物**：BE-01 对应模型/API/测试。
- **依赖**：CORE-001。
- **验收**：收藏/忽略刷新后保持；详情数据完整；人工数据和采集证据明确区分。

### CORE-003：关键词决策、趋势比较和实体图谱

- **实施内容**：keyword dismissal/merge lineage、trend compare、entity graph；补齐权限和大查询限制。
- **交付物**：BE-01 趋势与关系 API。
- **依赖**：CORE-001。
- **验收**：趋势/图谱可追溯到证据；合并可 dry-run、审计和回溯。

### CORE-004：机会人工工作流

- **实施内容**：机会创建、workflow stage、负责人、watcher、备注、证据关系、活动流、版本冲突；自动 stage 与人工状态边界明确。
- **交付物**：BE-02 模型/API/迁移/测试。
- **依赖**：CORE-001、002。
- **验收**：从情报转机会返回 created/existing；所有变更可回读和审计；并发冲突返回 409。

### CORE-005：结构化分析版本

- **实施内容**：analysis run、revision、编辑、引用、发布和导出输入；异步状态与 provider 失败处理。
- **交付物**：StructuredAnalysisRevision API 与 worker flow。
- **依赖**：CORE-004。
- **验收**：P10 展示真实 revision；发布版本不可静默覆盖；每个结论关联证据和算法/模型版本。

### CORE-006：迁移 P01–P10

- **实施内容**：按新模板连接真实接口；删除 mock import；实现 loading/error/partial/permission；完成所有动态 ID。
- **交付物**：P01–P10 产品页面和页面级测试。
- **依赖**：SAMPLE-006、CORE-002–005。
- **验收**：P01–P10 production 无 mock；所有写操作真实；核心闭环 E2E 通过。

## 9. PLAN-06：研究闭环（P11–P13）

目标：新增真正的研究工作流、步骤、任务、结果和发布能力。

### RES-001：研究领域模型与迁移

- **实施内容**：ResearchWorkflow、Step、Task、Result、EvidenceLink、Activity；定义状态机、public ID、版本和索引。
- **交付物**：数据库迁移、domain model、state transition tests。
- **依赖**：CORE-001、004。
- **验收**：非法状态跳转被拒绝；迁移可升级/回滚；OpportunityResearch 兼容策略明确。

### RES-002：工作流生命周期 API

- **实施内容**：列表、创建、详情、pause/resume/cancel；权限、幂等和并发控制。
- **交付物**：ResearchWorkflow API。
- **依赖**：RES-001。
- **验收**：重复请求不产生重复 workflow；状态可回读；取消/暂停不丢活动历史。

### RES-003：步骤、任务与重试

- **实施内容**：step attempts、task assign/status、retry；保留旧错误和输出。
- **交付物**：Step/Task API、worker integration。
- **依赖**：RES-002。
- **验收**：重试创建新 attempt；失败可诊断；负责人和任务状态可审计。

### RES-004：研究结果、证据与发布

- **实施内容**：result read/edit/version、证据引用完整性、publish、发布后通知 job、导出数据源。
- **交付物**：ResearchResult API。
- **依赖**：RES-003；通知可先以 job 状态占位。
- **验收**：发布前验证证据；发布事务和通知发送状态分开；历史版本不可被覆盖。

### RES-005：迁移 P11–P13

- **实施内容**：工作流列表、详情 stepper、任务、活动、结论与发布 UI；使用实体详情和分析模板。
- **交付物**：P11–P13 和 E2E。
- **依赖**：RES-002–004；SAMPLE-006。
- **验收**：新建→运行→失败重试→完成→发布闭环通过；无假进度和固定 RES ID。

## 10. PLAN-07：来源与运行闭环（P14–P21）

目标：完成“来源→配置/健康→监控计划→运行→日志/产出→分析队列”。

### OPS-001：来源定义与安全配置

- **实施内容**：SourceDefinition、动态/部署管理边界、config schema、credential reference、draft/validate/activate。
- **交付物**：BE-05 来源模型/API/secret tests。
- **依赖**：CORE-001。
- **验收**：秘密不回显、不入日志/审计；不支持在线修改的字段明确只读。

### OPS-002：来源测试与健康历史

- **实施内容**：test run、health series、incident、按来源 runs/observations；统一时间窗和指标口径。
- **交付物**：source health/history APIs。
- **依赖**：OPS-001。
- **验收**：P15/P16 统计可追溯到 run；测试数据不污染正式统计。

### OPS-003：监控计划领域

- **实施内容**：MonitoringPlan、schedule/timezone/sources/query、pause/resume、template、run request；编排现有 ProbeTask。
- **交付物**：BE-04 plan APIs 和 scheduler integration。
- **依赖**：OPS-001。
- **验收**：PLAN 是稳定产品实体；重复 run-now 不重复创建；时区和 schedule 有确定语义。

### OPS-004：运行详情、日志、产出和重试

- **实施内容**：run public ID、stage events、logs、outputs、关联对象、retry；日志脱敏和分页/流式。
- **交付物**：BE-04 run APIs。
- **依赖**：OPS-003。
- **验收**：失败运行可定位阶段和错误；retry 创建关联 run；下载使用短期授权。

### OPS-005：分析队列产品接口

- **实施内容**：task view、worker load、priority、single retry/cancel；与 admin run-pending 分离。
- **交付物**：analysis queue APIs。
- **依赖**：CORE-005；OPS-004 可并行。
- **验收**：队列项有真实 ID 和状态；权限限制单项动作；worker 竞争有测试。

### OPS-006：迁移 P14–P21

- **实施内容**：按列表/详情/分析模板重做来源、健康、计划、运行和队列页面；接真实接口。
- **交付物**：P14–P21、响应式截图和 E2E。
- **依赖**：OPS-001–005；SAMPLE-006。
- **验收**：来源→计划→运行→错误→重试 E2E 通过；不存在固定 PLAN/RUN ID。

## 11. PLAN-08：告警与治理闭环（P22–P34）

目标：完成告警处理、组织管理、账户安全、集成、审计、诊断、搜索和系统页面。

### GOV-001：告警规则扩展与通知中心

- **实施内容**：rule delete/test/template/export、event batch status、Notification、未读状态、notification preferences；投递状态独立。
- **交付物**：BE-06 API/模型/测试。
- **依赖**：CORE-001；关联 research/run 在 PLAN-06/07 完成后接入。
- **验收**：规则测试不污染正式统计；批量处理逐项返回；顶栏未读数真实。

### GOV-002：Workspace 与成员邀请

- **实施内容**：workspace settings、logo、数据管理 job、邀请/重发/撤销/接受；最后 OWNER 不变量继续有效。
- **交付物**：BE-07 workspace/membership APIs。
- **依赖**：CORE-001。
- **验收**：邀请不依赖临时明文密码；删除/清理要求再认证和异步 job；所有管理动作审计。

### GOV-003：角色权限产品决策与 API

- **实施内容**：先提供内置角色/权限只读 API；产品确认是否需要自定义角色。若需要，单独实现 Role/Permission/Binding，不允许编辑内置 OWNER 核心权限。
- **交付物**：决策记录、RBAC read API；可选 custom-role 子计划。
- **依赖**：GOV-002。
- **验收**：P26 不再硬编码权限矩阵；无 custom role 时编辑按钮不出现。

### GOV-004：账户安全第一阶段

- **实施内容**：self password change/reset、session list/revoke、TOTP enroll/confirm/disable、recovery code rotate、近期认证。
- **交付物**：BE-07 security APIs、安全测试和操作手册。
- **依赖**：CORE-001；独立安全评审。
- **验收**：恢复码只显示一次且哈希存储；敏感动作 step-up；会话撤销立即生效。

### GOV-005：SSO、Passkey 与通用集成决策包

- **实施内容**：分别评审 OIDC/SAML、WebAuthn、Integration catalog/OAuth PKCE/secret reference；不要与 TOTP 一次提交。
- **交付物**：ADR、威胁模型、分阶段接口；确认后实现。
- **依赖**：GOV-004；OPS-001 的 secret 经验可复用。
- **验收**：OAuth state 一次性且过期；WebAuthn challenge 防重放；secret 不回显；未完成能力不显示成功。

### GOV-006：全局搜索

- **实施内容**：统一 search envelope、类型过滤、权限裁剪、highlight、cursor；先接 observation/opportunity/keyword，再接 research/run。
- **交付物**：BE-08 search API 和 relevance tests。
- **依赖**：CORE-002、004；完整类型依赖 RES/OPS。
- **验收**：结果可直达真实 public ID；VIEWER 不看到无权对象；不在前端拉全量数据过滤。

### GOV-007：审计、诊断和统一导出

- **实施内容**：audit cursor/filter/detail、diagnostic snapshot/run、export jobs/short-lived download；secret scan 和数据分类。
- **交付物**：BE-08 APIs、worker jobs、审计测试。
- **依赖**：CORE-001；OPS-004 可复用 job/run 模式。
- **验收**：大导出不阻塞 API；诊断不泄露环境和堆栈；每个导出有 actor/filter/rows/hash。

### GOV-008：迁移 P22–P34

- **实施内容**：告警、规则、工作区、成员、角色、安全、集成、审计、诊断、搜索、登录、403/404；按六类模板重构。
- **交付物**：P22–P34、权限矩阵测试和 E2E。
- **依赖**：GOV-001–007；SAMPLE-006。
- **验收**：角色场景全部通过；危险动作不与普通动作混排；无“人工客服已接入”等虚假外部动作。

## 12. PLAN-09：全局 QA 与发布

目标：证明这是一套真实、稳定、可恢复的产品，而不只是视觉完成。

### QA-001：单元与组件测试

- **实施内容**：设计 token、组件状态、hooks、formatters、权限和状态机单测。
- **交付物**：前后端 unit suite。
- **依赖**：随各任务增量完成。
- **验收**：关键逻辑和状态转换有正反用例；新增代码不依赖只看截图验收。

### QA-002：API 契约与数据库迁移测试

- **实施内容**：OpenAPI diff、schema validation、权限、幂等、409、迁移 upgrade/downgrade、SQLite/PostgreSQL 路径。
- **交付物**：contract/migration CI。
- **依赖**：所有 backend 计划。
- **验收**：旧客户端兼容或有明确 breaking version；迁移可重复执行；PostgreSQL 并发关键路径通过。

### QA-003：业务 E2E

- **实施内容**：登录；信号→机会；机会→研究；来源→计划→运行→重试；告警→处理；成员邀请；安全会话；搜索→详情。
- **交付物**：浏览器 E2E suite。
- **依赖**：PLAN-05–08。
- **验收**：成功和失败路径均覆盖；刷新后状态保持；E2E 使用真实 API test environment。

### QA-004：视觉与响应式回归

- **实施内容**：五档视口截图；真实长文本、极端数字、空/错误/partial；检查布局位移和页面溢出。
- **交付物**：visual regression suite 和基准图。
- **依赖**：所有 UI 页面迁移。
- **验收**：390/768/1024/1280/1536 无文档级横向滚动；差异需人工批准；关键列不逐字换行。

### QA-005：可访问性

- **实施内容**：axe、键盘全流程、screen reader spot check、200% zoom、reduced motion、对比度。
- **交付物**：a11y report。
- **依赖**：UI-008、所有页面。
- **验收**：无 critical/serious axe 问题；核心流程只用键盘可完成；dialog 焦点正确。

### QA-006：性能与稳定性

- **实施内容**：路由分包、请求 waterfall、表格/图谱大数据、API p95、worker/backpressure、缓存、bundle budget。
- **交付物**：performance report 和预算门禁。
- **依赖**：业务功能完成。
- **验收**：关键页面达到项目批准的 Web Vitals/API 预算；10k 级列表使用服务端分页/虚拟化；失败不触发请求风暴。

### QA-007：安全复核

- **实施内容**：RBAC、CSRF、session、MFA、OAuth、SSRF、导出、日志、CSP、依赖、secret scan、审计完整性。
- **交付物**：security gate 和修复记录。
- **依赖**：PLAN-05–08。
- **验收**：高危/严重问题为零；秘密不出现在 response、bundle、日志、导出和审计 detail。

### REL-001：灰度与回滚

- **实施内容**：React 入口 feature flag/版本开关、数据库迁移顺序、静态资源缓存、监控、回滚演练。
- **交付物**：release runbook、rollback runbook。
- **依赖**：QA-001–007。
- **验收**：可以在不回滚数据库破坏性变更的情况下切回旧入口；关键指标和错误率可观测。

### REL-002：退休旧前端

- **实施内容**：React 稳定后移除默认旧静态入口和重复构建；保留必要迁移说明，不长期维护两套 UI。
- **交付物**：旧 UI retirement PR、文档更新。
- **依赖**：REL-001 灰度稳定并经人工批准。
- **验收**：仓库只有一套默认产品前端；CI、Docker、README 和运维文档指向同一入口。

## 13. 每个任务的统一 Definition of Done

一个任务只有同时满足以下条件才能标记完成：

1. 代码、类型、OpenAPI/契约和数据库迁移一致。
2. 有 loading、empty、error、partial、permission、rate-limit 中适用的状态。
3. 写操作只有收到真实成功结果后才显示成功；异步操作显示 queued/running/final。
4. 服务端执行权限、输入校验、幂等/并发保护和审计。
5. 390/768/1024/1280/1536 适用布局通过，不新增 10px/11px 交互文字。
6. 键盘、焦点、语义和对比度通过。
7. 单元/契约/集成/E2E 中适用测试通过。
8. 提供 before/after 截图、失败态截图和验证命令。
9. 文档和页面—能力—接口矩阵同步更新。
10. 没有引入新的 production mock、硬编码实体 ID、明文 secret 或假成功。

## 14. 首批建议启动任务

优先开始以下不会互相阻塞的任务：

1. BASE-001～004：冻结范围和门禁。
2. VIS-001～003：视觉原则、token、页面模板。
3. FE-001、FE-007：前端目录和生产发布链路。
4. CORE-001：public ID、bootstrap、错误契约。

第一批完成后并行推进：

- UI-001～008：公共组件。
- FE-002～006：数据和权限基础。
- CORE-002～005：核心后端接口。

五个样板页必须在批量迁移前通过 SAMPLE-006。后端领域任务可以继续并行，但 UI 不应在样板规则未冻结前复制到全部 34 页。
