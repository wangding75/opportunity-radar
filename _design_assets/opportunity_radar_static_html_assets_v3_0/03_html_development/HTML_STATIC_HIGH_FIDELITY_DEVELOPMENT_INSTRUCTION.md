# Opportunity Radar — 高保真静态 HTML 开发总指令

## 任务目标

读取 `opportunity_radar_static_html_assets_v3_0` 资产包中的：
- 34 张主体页面参考图；
- 27 张状态参考图；
- 页面矩阵；
- 状态矩阵；
- 跳转与导航矩阵；
- 交互规则；
- AppShell / Design Token 规范；
- HTML 实现修正规则；

开发出一个**高保真、可点击、可通过 URL 独立访问的静态 HTML Prototype**。

最终目标是：
1. 页面视觉与冻结图片高度一致；
2. 公共 AppShell 在所有页面完全统一；
3. 页面之间可以真实点击跳转；
4. Drawer / Modal / 状态流转可以实际操作；
5. 所有数据为本地 Mock，禁止伪装真实后端；
6. 产物可直接作为后续真实前端开发的视觉与交互基线。

---

# 0. 开始前强制读取顺序

在写任何代码之前，必须依次完整读取：

1. `README.md`
2. `02_product_spec/matrices/PAGE_MATRIX_V3.0.json`
3. `02_product_spec/matrices/STATE_MATRIX_V2.0.json`
4. `02_product_spec/navigation/ROUTE_AND_NAVIGATION_MATRIX.csv`
5. `02_product_spec/navigation/routes.json`
6. `02_product_spec/interaction/IMPLEMENTATION_OVERRIDES.md`
7. `02_product_spec/interaction/STATIC_HTML_INTERACTION_CONTRACT.md`
8. `02_product_spec/interaction/KEY_ACTION_MATRIX.csv`
9. `02_product_spec/app_shell/APP_SHELL_AND_DESIGN_TOKENS.md`
10. `03_html_development/HTML_DEVELOPMENT_ORDER.md`

然后逐页读取对应 PNG。

不得只看文件名开发。
不得跳过图片直接凭页面名称自行设计。

---

# 1. 图片读取规则

每开发一个页面：

1. 从 `PAGE_MATRIX_V3.0.json` 获取：
   - 页面 ID
   - 中文标题
   - route
   - active primary nav
   - reference_path
2. 打开对应参考 PNG。
3. 分析：
   - AppShell
   - 页面分区
   - Card 边界
   - 表格列
   - 图表
   - 文本层级
   - Tab
   - Filter
   - CTA
   - 空间关系
4. 用真实 HTML/CSS/SVG/JS 重建。
5. 禁止将 PNG 本身作为页面背景或整页 `<img>`。

状态稿同理：
先读取父页面 PNG，再读取状态 PNG。
状态必须建立在父页面真实 DOM 上。

---

# 2. 技术实现要求

优先使用现有项目技术栈；如果当前目录没有前端项目，则创建轻量静态原型工程。

推荐：
- Vite
- React + TypeScript
- CSS Modules / plain CSS
- React Router
- Lucide 或同风格 SVG icon
- SVG / lightweight chart implementation

如果不使用 React，也必须保证：
- 公共组件复用；
- 路由；
- 状态；
- 可点击交互；
- 无复制 AppShell。

禁止引入沉重后台管理模板。

---

# 3. 公共 AppShell 必须先做

必须先完成并冻结：
- Sidebar
- Topbar
- Global Search
- Domain selector
- Notification
- User menu
- Page container
- Tabs
- Filters
- KPI Card
- Table
- StatusBadge
- Drawer
- Modal
- Toast

所有业务页只组合这些基础组件。

必须遵守：
`02_product_spec/interaction/IMPLEMENTATION_OVERRIDES.md`

特别是：
- P14 一级导航必须高亮“监控”；
- P28-S01 必须复用 P28 AppShell；
- P31-S01 必须复用 P31 AppShell；
- P04 HTML 按 1536×1024 统一画布实现。

---

# 4. 路由

路由以：
`02_product_spec/navigation/routes.json`
和：
`ROUTE_AND_NAVIGATION_MATRIX.csv`
为唯一确定性来源。

主体页必须可以直接 URL 访问。

Drawer/Modal 推荐：
`?state=P03-S01`

示例：
`/intelligence/INT-20260819-01842?state=P03-S01`

刷新浏览器后应恢复对应状态。

---

# 5. 状态实现

禁止为 Drawer/Modal 状态复制整套页面。

正确模式：

```tsx
<AppShell>
  <OpportunityDetail />
  {state === "P09-S02" && <AssignOwnerDrawer />}
</AppShell>
```

P31-S01：
只切换搜索结果内容区域。

P32-S01：
复用登录品牌壳，右侧 Login Card 切换到 MFA 状态。

---

# 6. 静态交互

当前阶段不连接后端。

必须 Mock：
- 搜索
- 筛选
- Tab
- 分页
- 状态切换
- Drawer
- Modal
- Toast
- 创建成功 / 失败状态
- Run / Queue / Alert 状态
- 权限申请流程
- MFA 流程

明显可点击控件不得无反应。

如果某可见控件没有明确跳转目标：
优先执行合理的页面内状态变化或 Toast，
不得凭空新增业务页面。

---

# 7. 数据一致性

同一业务对象跨页面必须保持一致：

示例：
- `OPP-20260819-021`
- `RUN-20260819-1048`
- `TASK-20260819-00482`
- `AL-20260819-01528`

相同对象的：
名称、状态、负责人、评分、关联关系
不得在不同页面随机变化。

建议建立：
`src/mock/data.ts`

集中维护 Mock 数据。

---

# 8. 高保真要求

目标不是“类似”，而是按照冻结图片进行布局复刻。

必须重点对齐：
- 页面整体密度
- 左右边距
- Sidebar/Topbar
- Card 尺寸
- 字体层级
- 表格列宽
- 行高
- Badge
- Drawer 宽度
- 图表占比
- Button 层级
- 空白区域
- 分隔线

不要把高信息密度页面简化成几个大卡片。

---

# 9. 视觉验证

每完成一个页面或状态：

1. 启动本地静态服务；
2. 使用浏览器打开对应 URL；
3. 设置 viewport：
   `1536 × 1024`
4. 截图；
5. 与 reference PNG 并排比较；
6. 修复明显偏差。

必须保留：

```text
_evidence/
  P01/
    reference.png
    actual.png
  ...
```

状态稿同样保留证据。

不能只说“视觉相似”而不截图。

---

# 10. 自动检查

至少实现：

- 所有 34 个主体 route 可以打开；
- 所有 27 个 state 可以通过 URL/state 打开；
- 页面无 JS console error；
- 页面无 404 asset；
- 所有明显主按钮可点击；
- 一级导航跳转正确；
- Drawer 可以关闭；
- browser Back 可工作；
- P32-S01 保留 `returnTo`；
- P33-S01 保留 resource route；
- P14/P28/P31 Override 检查。

输出：
`STATIC_HTML_VALIDATION_REPORT.md`

---

# 11. 页面开发顺序

严格读取：
`03_html_development/HTML_DEVELOPMENT_ORDER.md`

先 AppShell，再主体页面，再状态。

不得一开始 61 页同时散开开发。

---

# 12. Git 规则

开始前：
- 检查工作区状态；
- 不覆盖已有未提交代码。

按开发阶段小步提交。

每个提交必须：
- 可启动；
- 无明显破损；
- 对应阶段截图证据存在。

禁止：
- amend
- rebase
- squash
- force push

除非用户明确要求，否则不要 push。

---

# 13. 最终交付

必须交付：

```text
static-html/
src/
public/
_evidence/
docs/
  PAGE_ACTION_MATRIX_IMPLEMENTED.csv
  STATIC_HTML_VALIDATION_REPORT.md
  VISUAL_REVIEW.md
README.md
```

README 必须写清楚：
- 安装命令
- 启动命令
- 访问 URL
- 页面数量
- 状态数量
- Mock 数据说明

最终回执必须包含：
- 主体页面完成数 / 34
- 状态完成数 / 27
- Route smoke 结果
- Console error 数量
- 视觉未收敛页面列表
- Deferred / 未实现交互列表
- Git commit
- 工作区状态

---

# 14. 完成判定

只有同时满足以下条件才可报告 PASS：

- 34 / 34 主体 HTML 页面完成；
- 27 / 27 状态完成；
- 61 个 reference 均有对应 HTML 视觉实现；
- 路由全部可访问；
- 关键交互全部可点击；
- AppShell 无跨页漂移；
- P14/P28/P31 Review 问题已在 HTML 中消除；
- 无整页 PNG 冒充 HTML；
- 无明显 console error；
- 截图证据完整。

若其中任何一项未完成：
必须报告 `BLOCKED` 或 `NOT_COMPLETED`，
不得用“基本完成”“已实现核心页面”冒充全量完成。
