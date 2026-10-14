# React 产品化基线

日期：2026-09-04  
范围：根目录 React 原型（`src/`）与其对应 FastAPI 服务。  
UI 基准提交：`861f8842167a8c4d3069e03e5232f65c88487875`（工作区含尚未提交的原型文件）。

## 范围裁决

根目录 React 原型是产品 UI 的唯一目标实现；`frontend/` 只用于复用既有 API 契约、权限规则和发布经验，不能继续作为新页面的并行实现。当前 React 原型尚未成为生产默认入口，此状态在 FE-007 之前保持明确：它是受构建、测试和视觉基线保护的候选产品前端，而不是已发布页面。

## 当前可复现基线

| 项目 | 当前值 | 复现方式 | 说明 |
|---|---:|---|---|
| React 主页面 | 34（P01–P34） | `node scripts/smoke_test.js` | 页面清单来自产品矩阵 |
| 状态设计 | 27 | `node scripts/smoke_test.js` | 使用 `?state=` 路由状态 |
| 路由 smoke | 61 / 61 通过 | 启动 Vite 后 `npm run test:smoke` | 仅验证 HTTP 与运行时错误，不代表业务闭环 |
| React 类型检查/构建 | 通过 | `npm run build` | 2026-09-04 已验证 |
| 后端单元测试 | 379 通过 | `cd backend; python -m pytest` | 2026-09-04，约 62 秒 |
| 当前 CI 正式前端 | `frontend/` | `.github/workflows/ci.yml` | 根 React 原型此前未纳入 CI |

## 已知视觉与产品风险

1. `viewport` 固定为 1536，且禁止缩放；在 1024px 已有约 1032px 的横向内容宽度，在 390px 无响应式重排。
2. 字号 token 的主体从 12px 起，页面中仍有大量 10px/11px 文字；阅读、状态和表格密度都低于生产可用阈值。
3. 以均权卡片堆叠为主，P01、P09、P24 尤其缺少页面主次和留白节奏；P02 的固定预览区压缩了表格可读性。
4. 34 页仍使用 mock 数据和 toast 假成功；没有统一 API、鉴权、路由实体参数和失败态机制。
5. React 没有生产静态构建、SPA deep-link fallback、自托管字体或 CSP 对齐，因此不能直接替换现有入口。

详细结论见 [全局评审](REACT_PROTOTYPE_GLOBAL_REVIEW.md)、[视觉重设计规范](REACT_VISUAL_REDESIGN_SPEC.md) 和 [后端开发计划](REACT_PROTOTYPE_BACKEND_DEVELOPMENT_PLAN.md)。

## 视觉采集基线

执行 `npm run test:ui-baseline` 会启动一个临时 Vite 服务，采集 P01、P02、P09、P24、P32 在 1536、1440、1280、1024、390 五档视口的截图与横向溢出、最小计算字号、可见元素数等指标。输出默认写到本地 `_evidence/react-ui-baseline/`；它是评审证据，不应作为构建产物提交。

实际首次采集（P01/P02/P09/P24/P32 × 五档视口）显示 25 个样本中有 6 个页面级横向溢出：P01 在 1024px、390px，P02/P09/P24/P32 在 390px；全部样本最小计算字号为 10px。这些是重构前基线，不是可接受阈值。截图和 `report.json` 位于本地 `_evidence/react-ui-baseline/`。

2026-09-04 的样板页重构后复测显示，同一 25 个样本的 `horizontalOverflow` 均为 `false`，最小计算字号为 12px。该结论仅覆盖 P01、P02、P09、P24、P32 的视觉样板与响应式布局；不代表其 mock 数据、写操作、权限和全部异常状态已经完成生产验收。

## 基线使用规则

1. 每个 UI PR 要附同一页面、同一视口的前后截图，并解释布局主次变化。
2. 所有 `horizontalOverflow=true` 均为阻断项，除非该区域明确标注为数据表横向滚动容器并存在等价窄屏视图。
3. 正文/表单/按钮文字不得低于 14px；图表标签和表格辅助信息不得低于 12px。
4. 性能、无障碍和视觉阈值在 PLAN-09 固化为发布门禁；基线脚本用于在重构期间持续发现退化。
