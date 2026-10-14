# HTML Implementation Overrides — Mandatory

本文件优先级高于单张设计图中出现的公共导航差异。

## 1. 公共 AppShell

除 P32 登录、P33/P34 最小化状态页外，主体页面统一采用同一个 `AppShell`。
禁止每页复制一套 Sidebar/Topbar。

一级导航固定且只允许：
1. 今日雷达
2. 情报
3. 机会
4. 研究
5. 监控
6. 设置

模块高亮：
- P01：今日雷达
- P02–P07：情报
- P08–P10：机会
- P11–P13：研究
- P14–P23：监控
- P24–P30：设置
- P31：不新增搜索一级导航
- P32：不使用业务 AppShell
- P33/P34：使用最小化 AppShell

## 2. Review 中发现的图片冲突

### P14
P14 图片公共导航存在错误。HTML 实现必须：
- 一级导航高亮 `监控`
- 来源相关页使用同一来源/监控导航体系
- 不得按图片错误高亮 `设置 / 角色与权限`
P14 主体内容仍按图片高保真还原。

### P28-S01
该状态图的 Shell 与 P28 父页面有差异。
HTML 必须实现为：
`P28 Base Page + P28-S01 Drawer`
不得复制状态图中的另一套导航。

### P31-S01
该状态图的 Shell 与 P31 父页面有差异。
HTML 必须实现为：
`P31 Global Search Base Page + No Results Content State`
不得新增左侧“工作区/收藏夹/我的任务”等导航。

### P04
图片画布尺寸与其他稿不一致。
HTML 统一按 1536×1024 baseline 布局，不需要保留 P04 原图画布尺寸差异。

## 3. 状态父页面修正

- P17-S02 主入口：P17；P18 也可调用同一状态。
- P17-S03 父页面：P18。
- P27-S01 成功后回 P27。
- P32-S01 是未来登录时的 MFA 状态，不是 P27-S01 的直接出口。

## 4. State 实现方式

以下状态禁止做成复制整个页面的新 HTML：
- 所有 Drawer/Modal 状态
- P28-S01
- P22-S01
- P23-S01
- P25-S01
- P26-S01
- P27-S01/S02

应使用：
`ParentPage + Overlay Component`

P31-S01、P32-S01 属于 Content State，可替换页面主内容区域但仍复用正确 Shell。
