# React 原型全局 Review 与 UI 优化方案

日期：2026-09-04  
评审基准：根目录 `src/` 的 Opportunity Radar 3.0 React 原型  
不作为目标实现：`frontend/` 与 `backend/app/static/` 中的旧 TypeScript UI

## 1. 结论

新 React 原型已经完整覆盖 34 个页面和 27 个状态，视觉结构、业务对象和跨页路径足以作为后续产品实现的 UI 基准；但它当前仍是高保真静态原型，不是可发布产品前端。

阻断真实上线的三个首要问题是：

1. `src/` 中没有 API、登录会话、CSRF、RBAC 或服务端持久化，页面读取固定 mock，114 处 `showToast(...)` 中大量操作直接报告“成功”。
2. 排版整体偏小且密度失控：正文基准 14px，导航/输入 13px，次要操作 12px，代码中还有大量 10px/11px 文本；1280px 的情报列表已经因主从双栏发生严重换行。
3. 没有响应式策略。1024px 时六列 KPI 逐字换行；390px 时文档横向宽度仍为 1032px，侧栏仍占 176px。

因此不建议直接做一次全局 `font-size + 2px`。字号只是表象，真正需要重做的是页面构图、信息主次、空间节奏、表面层级和交互反馈。正确顺序是：先确定视觉方向与页面模板，再建立响应式布局和信息优先级，然后调整字号 token，最后逐页消除局部 10px/11px 与行内样式。

完整的布局、色彩、卡片、表格、图表、页面模板和核心页面重排规范见 [`REACT_VISUAL_REDESIGN_SPEC.md`](REACT_VISUAL_REDESIGN_SPEC.md)。

完整执行顺序、任务依赖、交付物和验收条件见 [`REACT_OPTIMIZATION_EXECUTION_PLAN.md`](REACT_OPTIMIZATION_EXECUTION_PLAN.md)。

## 2. 已验证事实

| 检查 | 结果 | 含义 |
|---|---:|---|
| 根 React TypeScript | `tsc --noEmit` 通过 | 类型层面可编译 |
| 34 页面 + 27 状态 smoke | 61/61 路由返回成功 | 仅证明路由能加载，不证明交互真实可用 |
| 后端 pytest | 379 passed | 现有 FastAPI 基线稳定，可在其上补接口 |
| React API 调用 | 0 | 新原型未接后端 |
| `showToast(...)` | 114 处 | 许多按钮只有本地反馈 |
| TSX 行内 `style={{...}}` | 2,217 处 | 响应式、主题和一致性难以集中治理 |
| 10px / 11px 字面字号 | 173 / 263 处 | 小字不是个别页面问题 |
| CSS `@media` | 0 | 没有断点实现 |
| 1024px 实测 | `scrollWidth=1032`，六列 KPI 严重折行 | 平板/小屏笔记本不可用 |
| 390px 实测 | `scrollWidth=1032` | 移动端发生大范围横向溢出 |

现有 smoke 脚本只检查页面 HTTP 状态和 console/page error，没有断言页面内容、交互结果、响应式、可访问性或 API 请求，因此不能作为“功能完成”的验收证据。

## 3. 按严重程度排序的问题

### P0 — 原型与产品运行链路断开

- 页面数据来自 `src/mock/data.ts` 或组件内硬编码数据，没有 loading/error/empty/stale 的真实请求状态。
- 收藏、订阅、创建机会、修改状态、分配负责人、发布研究、手动运行、规则保存、邀请成员、MFA、OAuth 修复等按钮多数只修改局部 state、打开状态层或弹 toast。
- `backend/app/main.py` 仍只发布 `backend/app/static/`；当前 Dockerfile 不构建根 React 应用。
- React 使用 History API 路径，如 `/today`、`/opportunities/...`，但 FastAPI 只为 `/` 返回旧静态首页，没有 SPA fallback；直接刷新深层链接会 404。
- `index.html` 从 Google Fonts 加载 Inter，而现有后端 CSP 仅允许 `style-src 'self'`，部署到现有服务后字体请求会被阻止。生产环境也不应依赖外部字体可达性。

处理方向：先完成构建/部署入口、API client、auth bootstrap、错误模型和真实查询状态，再逐页替换 mock。后端需求见 `REACT_PROTOTYPE_BACKEND_DEVELOPMENT_PLAN.md`。

### P0 — 鉴权和权限边界只存在于视觉稿中

- `/login` 只是本地表单状态，任何人可直接打开 `/settings/roles`、`/settings/security` 等路由。
- AppShell 固定显示“张天宇 / 高级分析师”，没有读取 `/api/v1/auth/me`。
- UI 没有基于 VIEWER / RESEARCHER / ADMIN / OWNER 隐藏或禁用操作，也没有统一处理 401、403、429、会话过期和 CSRF。
- `/access-denied` 是一个可访问页面，不是权限守卫的结果。

处理方向：建立 `AuthProvider + PermissionGate + ApiClient`。服务端继续作为最终授权边界，前端只负责减少误操作和提供清楚反馈。

### P1 — 整体视觉缺少明确重心，呈现为同质化卡片墙

- P01 首屏同时出现 6 个 KPI、3 个中部卡片和 3 个底部卡片，所有容器都使用相近的白底、细边框和圆角，用户无法快速判断“今天最值得处理的事情”。
- P09 等详情页把评分、市场规模、竞争强度、壁垒做成四个同权卡片，又在下方继续堆卡片；核心结论、证据与主操作没有形成视觉主线。
- P24 设置页把基本信息、研究范围、策略、存储、通知和危险操作都做成相近大小的盒子，阅读顺序依赖坐标而不是语义。
- 全局大量使用浅灰边框划分区域，导致页面“盒子很多但层级很弱”；卡片、表格、抽屉、状态块之间缺少不同的表面语义。
- 蓝、紫、绿、黄、红、青被频繁用于装饰图标和标签，语义色与品牌色混用，画面活跃但不够克制，也削弱真正风险状态的注意力。
- 页面普遍横向铺满，缺少适合阅读的正文列宽和稳定对齐线；同时留白集中在卡片内部，卡片之间与章节之间的节奏差异不足。

处理方向：采用“安静、可信、可行动的情报工作台”视觉语言。每屏只建立一个主要视觉重心和一个主要动作；用页面分区与留白组织信息，减少无意义卡片；颜色主要表达品牌、状态与风险，不承担随机装饰。

### P1 — 字号、行高与对比度不足

当前 token：`xs=12`、`sm=13`、`base=14`、`md=15`、`lg=16`、`xl=18`、`2xl=20`、`3xl=24`。大量页面又绕过 token 写入 10px/11px。

建议改为以下语义化层级：

| 语义 | 建议字号/行高 | 使用约束 |
|---|---|---|
| Caption | 12/18 | 仅时间、辅助编号、图例；不可承担按钮或关键状态 |
| Compact body | 14/20 | 表格、筛选器、导航、按钮的最低字号 |
| Body | 16/24 | 摘要、说明、表单正文 |
| Section title | 18/26 | 卡片标题、抽屉分组 |
| Page subtitle | 16/24 | 页面标题下说明 |
| Page title | 28/36 | 一级页面标题 |
| KPI value | 28–32/36 | 关键数字，避免与标题争抢层级 |

补充规则：

- 交互控件不小于 14px；常规按钮高度至少 36px，主要表单控件 40px，触控目标 44px。
- 禁止使用 10px/11px 表达可操作文本、状态、表格核心值或图表坐标。
- `--text-muted: #94a3b8` 在白底上的对比度不足以承载当前大量 10–12px 文本。辅助文字至少提升到约 `#64748b`；更浅颜色只用于装饰或禁用态。
- 中文正文不依赖 Inter。字体栈优先本地系统中文字体，Inter 如需使用应自托管并只服务拉丁数字。
- 移除 `maximum-scale=1.0, user-scalable=no`，保留用户缩放能力。

### P1 — 响应式与信息密度失控

建议断点不是简单缩放，而是改变信息结构：

| 视口 | AppShell | KPI | 列表/详情 | 页面操作 |
|---|---|---|---|---|
| `>=1440` | 176px 侧栏 | 6 列 | 可使用主从双栏 | 标题右侧完整操作组 |
| `1200–1439` | 默认 64px 收起侧栏 | 3 列或 6 列紧凑 | 列表全宽，预览改抽屉 | 次要操作进 overflow menu |
| `768–1199` | 64px 图标栏或抽屉导航 | 2–3 列 | 表格按列优先级隐藏，详情单列 | 操作允许换行 |
| `<768` | 顶部栏 + 导航抽屉 | 1–2 列 | 表格改卡片列表，详情单列 | 底部/粘性主操作 |

重点页面：

- P01 今日雷达：六 KPI 在 1024px 已逐字换行；使用 `repeat(auto-fit, minmax(180px, 1fr))`，内容卡片在 1200px 以下改两列/单列。
- P02 情报列表：1280px 仍固定展示“表格 + 右侧预览”，标题和摘要被压成窄列。只有 `>=1440` 保留 master-detail；其余宽度点击行打开 Drawer。
- P03/P09/P10/P12/P13 等详情页：固定 `1fr + 340px/360px` 应在 1200px 下折为单列，右栏信息放到正文后或粘性摘要抽屉。
- P06/P07 图表：坐标文字目前 9–10px；应增加最小字号、可滚动/缩放和键盘可读的数据表替代视图。
- 所有数据表：定义 `required / important / optional` 列优先级；窄屏不能仅依赖水平滚动。
- P24–P30 设置页：二级导航、表单和危险操作在窄屏需拆为纵向分区，危险操作不能和普通设置使用同等视觉权重。

### P1 — 路由参数没有驱动实体数据

- 路由支持动态路径，但情报详情、机会详情、来源详情等页面固定读取第一个 mock 或固定实体。
- 从不同表格行进入详情时，URL 会变化，内容却可能仍显示同一个对象。
- 原型的 `OPP-...`、`INT-...`、`PLAN-...`、`RUN-...` 是字符串公共 ID，而现有部分后端路由使用数据库整数 ID。公共 ID 契约尚未统一。

处理方向：路由解析必须提供实体参数；页面查询 key 由参数组成；后端确定稳定 public ID，并保留必要的兼容读取。

### P1 — 可访问性不满足生产要求

- Modal/Drawer 没有 `role="dialog"`、`aria-modal`、标题关联、焦点圈定、打开后聚焦、关闭后焦点恢复和背景滚动锁定。
- 多个 `div`、`span`、`tr` 使用 `onClick`，键盘无法触发，也没有可读的 link/button 语义。
- 多个只有图标的按钮缺少明确名称；图表主要依赖颜色和鼠标悬浮。
- 全局 `button { outline: none; }` 移除了默认焦点提示，却没有完整的 `:focus-visible` 替代。
- toast 没有统一验证 `aria-live` 等级；错误和成功都容易只靠颜色传达。

处理方向：公共组件层一次修复，页面禁止自行实现交互容器。目标至少达到 WCAG 2.2 AA 的键盘、焦点、对比度和缩放要求。

### P2 — 前端架构难以持续维护

- 11,873 行 TSX 中有 2,217 处行内 style，断点、主题、hover/focus、密度模式无法集中管理。
- 页面同时承担布局、图表、数据、状态和动作，缺少 feature/domain 层。
- 没有 API schema 生成、query cache、form validation、错误边界和组件级测试。
- 34 个页面在 `App.tsx` 中同步 import，无法路由级分包。

建议目录边界：

```text
src/
  app/          # providers, router, auth, query client
  api/          # generated types, client, error normalization
  features/     # intelligence, opportunities, research, monitoring...
  components/   # design-system only
  layouts/      # shell, settings layout, auth layout
  mocks/        # dev/test only; production build不可引用
```

样式优先使用 CSS Modules、vanilla-extract 或项目统一的 utility 方案。关键不是更换技术，而是把 typography、spacing、breakpoint、状态和 focus 规则从页面行内样式迁到设计系统。

## 4. 推荐实施顺序

### UI-F0：运行链路与防假成功

- 接入真实 API client、会话、CSRF、RBAC、错误规范。
- production build 禁止引用 `src/mock/data.ts`。
- 未接通的写操作隐藏或禁用并解释，不允许成功 toast。
- 完成 SPA deep-link fallback 和字体/CSP 修复。

### UI-F1：视觉基础、页面模板与 AppShell

- 先落地 `REACT_VISUAL_REDESIGN_SPEC.md` 中的视觉方向、表面层级、页面模板、栅格和操作优先级。
- 落地新字号/行高/对比度、颜色、圆角、边框、阴影和 motion token。
- 实现 1440/1200/768 断点和侧栏/顶栏变化。
- 建立 `PageHeader` 的窄屏操作折叠规则。

### UI-F2：高密度页面重排

- 先处理 P01、P02、P08、P14、P17、P19、P21、P22、P23、P25、P29。
- 再处理所有双栏详情和图表页。
- 为表格定义列优先级与移动端卡片形态。

### UI-F3：公共组件可访问性

- Dialog/Drawer、Tabs、Toast、FilterBar、Pagination、Table、IconButton 统一修复。
- 清理非语义点击容器和 10px/11px 交互文字。

### UI-F4：测试门禁

- 关键业务交互使用 API mock contract test，而不是只检查 HTTP 200。
- 视口至少覆盖 1536×1024、1280×800、1024×768、768×1024、390×844。
- 加入 axe 可访问性检查、键盘 Tab 顺序、modal focus trap、无横向页面溢出断言。
- 每个写操作断言真实请求、失败态、重试态和最终服务端回读结果。

## 5. UI 验收标准

1. 5 秒测试中，用户能说出当前页面的主要结论、最重要风险和下一步主操作；首屏不能出现多个同权主按钮。
2. 同一页面最多使用三种 surface 层级；禁止卡片内继续堆同视觉权重卡片，纯分组优先用标题、留白和分隔线。
3. 页面、卡片、表格和详情栏拥有稳定对齐线；正文阅读列宽控制在约 640–760px，不让长段落横跨整个屏幕。
4. 390、768、1024、1280、1536 五档视口均无文档级横向滚动；明确标注为数据画布的局部容器除外。
5. 交互文本 computed font-size 不低于 14px；正文不低于 14px，默认正文 16px；12px 仅限高对比度辅助信息。
6. P02 在 1280px 不同时固定展示完整表格和 340px 预览栏。
7. 所有动态详情由 URL 参数读取对应实体，不能固定显示 mock 首项。
8. 所有成功提示之前必须获得 2xx 服务端响应；异步任务必须展示 job/run 状态，不能把 202 当成业务完成。
9. 未登录访问受保护路由跳转登录；无权限操作不渲染或给出明确 403 状态。
10. Modal/Drawer 支持 Esc、焦点圈定、关闭后焦点恢复、屏幕阅读器标题和背景滚动锁。
11. production bundle 中不存在 mock 业务记录，也不会向 Google Fonts 等未列入 CSP 的第三方发请求。
