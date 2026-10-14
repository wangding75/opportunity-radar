# 应用边界

- `app/`：Provider、入口、路由装配和全局错误边界。
- `api/`：唯一允许使用 `fetch` 的目录；页面只调用 feature hook 或 API 资源函数。
- `features/`：按业务域组织页面数据、mutation、权限与局部组件。
- `components/`：跨域设计系统组件；不得导入具体 feature。
- `layouts/`：六类页面模板与响应式布局。
- `mock/`：仅开发/测试 fixture。生产入口不允许导入它。

过渡期的 `pages/` 保留原型页面。页面迁移遵循“先接入模板和 feature 数据层，再删除页面内 mock 与 toast”的顺序，避免将 34 页一次性搬动造成不可审查的大改动。
