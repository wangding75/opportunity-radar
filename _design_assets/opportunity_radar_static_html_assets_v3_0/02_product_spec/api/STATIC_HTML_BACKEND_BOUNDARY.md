# Backend Boundary for Static HTML Phase

本阶段只开发静态 HTML 原型。

所有后端能力统一标记：
`MOCK_ONLY_STATIC_HTML`

不得因为静态交互可点击，就把能力声明为 `SUPPORTED`。

未来接真实后端时再逐项核验：
- SUPPORTED
- NEED_BACKEND
- DEFERRED_UNAVAILABLE

静态阶段必须给未来 API 留出清晰组件边界，例如：
- Repository / service adapter
- async job status
- auth / permission adapter

但不得在本阶段虚构真实 API path。
