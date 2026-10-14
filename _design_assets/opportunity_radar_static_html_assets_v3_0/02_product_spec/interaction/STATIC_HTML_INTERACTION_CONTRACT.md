# Static HTML Prototype Behavior Contract

## 目标
本阶段交付是**高保真可点击静态 HTML Prototype**，不是后端功能完成证明。

## 所有可见控件都必须有行为
每个明显可点击元素必须属于以下一种：
1. 页面跳转；
2. 打开/关闭 Drawer；
3. 打开/关闭 Modal；
4. Tab 切换；
5. Filter/Dropdown 状态切换；
6. 表格选择/分页；
7. 本地 Mock 状态流转；
8. Toast 反馈。

禁止明显按钮点击无反应。

## Mock 数据
允许在静态 HTML 中使用本地固定数据。
必须满足：
- 与图片信息类型一致；
- ID/状态跨页面一致；
- 同一 Opportunity / Research / Run / Alert 在不同页面使用同一名称和 ID；
- 不把 Mock 行为标记成真实后端成功。

## URL
所有主体页面必须有可直接访问 URL。
Drawer/Modal 状态推荐：
`<parent-route>?state=Pxx-Syy`

刷新 URL 后应能恢复对应状态。

## 浏览器返回
- 打开 Drawer/Modal 后 Back 应关闭当前状态或回到上一 History。
- 页面跳转后 Back 应返回来源页面。
- Login MFA 和权限申请必须保留 `returnTo`。

## 状态持久化
仅需浏览器会话级本地状态：
- URL query
- `sessionStorage` / in-memory store
- 不要求服务端持久化

## 禁止
- 把整张 PNG 作为 `<img>` 覆盖页面实现。
- 把 PNG 作为 CSS `background-image` 冒充 HTML。
- 仅做不可点击截图。
- 为了视觉一致性复制多份 AppShell。
