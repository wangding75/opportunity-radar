# AppShell & Design Tokens — Static HTML Baseline

## Baseline
- 设计验收视口：1536×1024
- 页面必须在该视口下无纵向浏览器缩放、无整体截图背景。
- 图片是视觉参考，最终页面必须由真实 DOM/CSS/JS 构成。

## AppShell
公共组件：
- `AppShell`
- `Sidebar`
- `Topbar`
- `GlobalSearch`
- `DomainSelector`
- `NotificationBell`
- `UserMenu`
- `PageHeader`
- `Tabs`
- `FilterBar`
- `KpiCard`
- `DataTable`
- `StatusBadge`
- `Drawer`
- `Modal`
- `Toast`

### 建议几何基线
以下为 HTML 统一实现基线；最终以冻结图片视觉校准：
- Sidebar: 156–176px
- Topbar: 60–64px
- Page horizontal padding: 20–28px
- Content gap: 12–16px
- Card radius: 10–14px
- Drawer: 500–560px；高信息密度稿允许更宽
- Modal: 720–920px
- Table row: 42–52px

## CSS Tokens
必须统一定义 CSS variables，禁止页面内散落硬编码主题值：

```css
:root {
  --color-primary: #1677ff;
  --color-success: #13b76a;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;

  --text-primary: #13233b;
  --text-secondary: #71839b;
  --border-default: #e6ebf2;
  --surface-page: #f7f9fc;
  --surface-card: #ffffff;

  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 14px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
}
```

颜色可在视觉对比后微调，但必须全局统一。

## Typography
优先：
`Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif`

必须形成统一层级：
- Page title
- Section title
- Card title
- Body
- Metadata
- Table
- Badge

## 图表
- 必须用 HTML/SVG/Canvas 实现可视化。
- 禁止直接截取原图图表区域作为页面图片。
- 静态数据可以 Mock，但标签、量级和视觉结构应匹配参考图。

## Icon
使用统一 Icon 库或 inline SVG。
禁止不同页面混用风格明显不同的图标。
