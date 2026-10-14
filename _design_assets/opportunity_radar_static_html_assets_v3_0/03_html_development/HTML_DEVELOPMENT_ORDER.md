# HTML Development Order

## T01 AppShell / Tokens
先只实现公共结构和基础组件，不开发业务页。
验收：1536×1024，Sidebar/Topbar/Drawer/Table/Tabs/KPI/Badge 统一。

## T02 P01–P06
今日雷达、情报列表/详情、关键词、趋势。

## T03 P07–P13
关系图谱、机会池/详情、结构化分析、研究工作流/详情/结论。

## T04 P14–P23
来源、监控、Run、Analysis Queue、告警。
P14 必须按 `IMPLEMENTATION_OVERRIDES.md` 修正导航。

## T05 P24–P30
工作区、成员、权限、安全、集成、审计、系统诊断。
P28-S01 后续必须复用 P28 Shell。

## T06 P31–P34
搜索、登录、无权限、404。
P31-S01 必须复用 P31 Shell。

## T07 P03/P09 状态
P03-S01~S04、P09-S01~S05。

## T08 Research 状态
P11-S01、P12-S01、P13-S01。

## T09 Monitoring 状态
P17-S01~S03、P20-S01、P21-S01、P22-S01、P23-S01。

## T10 Governance / Security 状态
P25-S01、P26-S01、P27-S01/S02、P28-S01、P31-S01、P32-S01、P33-S01。

## T11 Interaction Audit
逐页点击所有明显按钮、Tab、Dropdown、表格行、分页、Drawer、Modal。
生成 `PAGE_ACTION_MATRIX_IMPLEMENTED.csv`。

## T12 Visual Regression
每张主体页/状态稿在 1536×1024 截图，与 reference 同名成对存放。
修复 AppShell、布局、字体、间距、图表、表格、Drawer。
