# React 页面模板归属

`src/layouts/PageTemplates.tsx` 是 34 个页面的唯一栅格来源。页面只能组合模板与公共组件；除数据可视化或确有业务理由的局部区域外，不得自行声明页面级 grid。

| 模板 | 页面 |
|---|---|
| 分诊工作台 `TriageLayout` | P01 |
| 列表工作台 `ListWorkspaceLayout` | P02、P04、P05、P08、P14、P17、P19、P21–P23、P25、P29、P31 |
| 实体详情 `EntityDetailLayout` | P03、P09、P12、P15、P18、P20 |
| 分析画布 `AnalysisCanvasLayout` | P06、P07、P10、P13、P16、P30 |
| 设置治理 `SettingsLayout` | P24、P26–P28 |
| 认证/状态 `FocusedStatusLayout` | P32–P34 |

P33/P34 可在需要上下文导航时保留 AppShell，但其内容区必须使用 `FocusedStatusLayout`。P32 保持独立认证 Shell，同时遵守同一窄屏和最小字号规则。
