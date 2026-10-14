# Opportunity Radar R04 中文业务闭环设计系统

## 核心目标
这是机会情报产品，不是 BI 大屏，也不是后台功能列表。所有用户可见文案必须使用简体中文；仅对象 ID、URL、版本号、技术日志可保留英文/ASCII。

## 功能能力边界
UI 不得伪造后端能力。未确认具备安全且语义等价接口的动作，不显示可执行主按钮，不模拟保存成功。
- 机会状态变更：未确认接口时只读。
- 研究生成/研究工作流：未确认接口时仅展示已有分析、任务和结果，不提供“生成/重新生成”。
- 调度控制/手动运行：未确认接口时仅展示计划和运行记录，不提供“立即运行/暂停”。
- 告警读状态/确认/关闭：未确认接口时只读浏览并跳转关联对象。
- 通知与集成设置：未确认接口时不做正式可编辑页面。
- 用户/角色写操作：未确认接口时只读。

## 一级导航
固定 6 项：工作台、机会、情报、研究、运行、管理。
- 情报：最新情报、关键词发现、关注关键词、趋势分析、关系图谱。
- 研究：结构化分析、研究任务、研究结果。
- 运行：数据源、监控计划、运行记录、分析队列、告警。
- 管理：用户与角色、审计日志、系统设置、系统诊断。
机会是产品核心对象，作为一级导航独立存在。

## 用户闭环
1. 工作台 → 重点机会 → 机会详情 → 证据 → 原始情报/来源 → 返回机会 → 已有研究/历史。
2. 最新情报 → 情报详情 → 关联机会 → 机会详情；或 → 来源详情 → 最近运行 → 运行详情。
3. 机会详情 → 已有结构化分析/研究结果 → 证据引用 → 来源/原始情报 → 返回研究/机会。
4. 运行/告警 → 关联运行 → 运行详情 → 数据源/监控计划 → 错误/心跳/队列 → 返回运行。
5. 管理只读状态 → 审计日志 → 事件详情 → 关联对象。
每个页面至少有一个明确的下一步对象，禁止孤岛页。

## AppShell 冻结
所有登录后桌面页共用唯一 AppShell：左侧导航 216px；品牌区 64px；顶栏 56px；内容区左右 24px、上下 20px。顶栏左侧全局搜索，右侧仅刷新（适用时）、通知、帮助、头像。PageHeader 只出现一次；详情页使用 EntityHeader。不同页面禁止重新生成不同尺寸 Shell。

## 页面模板
- 工作台：分诊页。重点机会、最新情报变化、运行异常、最近研究结果。最多 3 个紧凑摘要，不使用大 KPI 或圆环图。
- 列表页：PageHeader + FilterBar + DataTable/List + 分页。
- 详情页：EntityHeader + Tab，元数据只在头部出现一次。
- 运行页：紧凑状态条 + 主表格/日志，面向问题定位。
- 设置页：固定 SettingsFrame，无后端能力的设置项不出现可编辑控件。

## 视觉
Inter；中文回退 PingFang SC / Microsoft YaHei / system sans。主文字 #0F172A，次文字 #475569，背景 #F8FAFC，表面 #FFFFFF，边框 #E2E8F0，主色 #2563EB。默认无阴影，6–8px 圆角。禁止渐变、玻璃拟态、巨型卡片、卡片墙、装饰性大屏。

## 公共组件
AppShell、SidebarNav、TopBar、PageHeader、EntityHeader、TabBar、FilterBar、DataTable、StatusBadge、ScoreIndicator、ConfidenceBadge、SourceList、EvidenceList、Timeline、Drawer、Modal、EmptyState、ErrorState、ReadOnlyNotice、CapabilityUnavailableNotice、SettingsFrame。

## 中文文案
Overview=工作台；Opportunities=机会；Raw Intelligence=最新情报；Research Tasks=研究任务；Runs=运行记录；Alerts=告警；Settings=系统设置；Analysis Pending=待分析；High Confidence=高置信度。

## 生成验收
每屏检查：中文完整度、Shell 一致性、无重复信息、存在下一步路径、无虚假写按钮、不可用能力未伪装、无卡片堆叠/BI 大屏化/横向溢出。