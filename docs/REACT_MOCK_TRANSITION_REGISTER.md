# React mock 与假成功迁移登记

日期：2026-09-04。此表是 FE-006 的迁移清单；在接口完成前，相应动作必须显示为只读、禁用或“能力开发中”，不能显示业务成功。

| 位置 | 当前原型行为 | 处理方式 | 依赖 |
|---|---|---|---|
| P02/P03 | `MOCK_INTELLIGENCE`、收藏/订阅/详情 | 接入 observations 与用户状态后删除 | BE-01 |
| P08/P09 | `MOCK_OPPORTUNITIES`、关注/负责人/状态 | 接入机会工作流与 public ID 后删除 | BE-02 |
| P17 | `MOCK_MONITORING_PLANS`、新建/运行 | 接入 monitoring plan 后删除 | BE-04 |
| P19/P21 | `MOCK_RUNS`、`MOCK_QUEUE_TASKS` | 接入 run detail/queue 后删除 | BE-04 |
| P22 | `MOCK_ALERTS`、批量处理 | 接入 alert batch/export 后删除 | BE-06 |
| P25 | `MOCK_MEMBERS`、邀请 | 接入 invitation lifecycle 后删除 | BE-07 |
| StateOverlays | 创建、发布、同步、MFA、OAuth 等成功 toast | 每个 action 改为真实 mutation 或禁用 | BE-02–07 |

可保留的 UI-only 行为只有导航、折叠、排序/筛选视图、复制到剪贴板及纯展示偏好；它们的 toast 必须准确说明结果，例如“链接已复制”，不得暗示持久化。
