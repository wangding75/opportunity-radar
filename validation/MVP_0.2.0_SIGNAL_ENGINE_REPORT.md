# Opportunity Radar MVP 0.2.0 验收报告

日期：2026-08-12

## 结论

**PASS（MVP 0.2.0 代码完善范围）**

本轮补齐了从 Observation 到 Trend / Graph / Opportunity / Probe Plan 的核心分析链，并修复基线中会导致趋势失真、时间比较异常、陈旧热点长期污染、数据来源等级伪造和中文关键词截断的问题。

## 本轮完成

- KeywordRelation 共现图谱。
- KeywordTrendDaily 7 / 30 / 90 日时间序列。
- Keyword 生命周期按近期窗口衰减。
- Opportunity / OpportunityEvidence。
- Demand / Supply / Execution / Cross-source / Saturation / Business Risk 分离评分。
- Opportunity 旧证据衰减与 DORMANT 状态。
- Evidence Quality 权重。
- Probe Planner + Connector Capability 路由。
- 同日相同内容/指标幂等；跨日或 payload/App 版本变化保留新 Observation。
- 外部时区时间戳统一转换为 UTC naive datetime。
- Instrumented App Sanitizer。
- App Version Schema Drift 报告。
- Import Provenance 校验。
- `/ready` 数据库迁移就绪检查。
- Dashboard 增加 Opportunity 展示。
- Alembic 0002 迁移及基线遗漏索引补齐。
- 应用运行时移除 `Base.metadata.create_all()`。
- 中文关键词按标点/连接词分段，取消固定 8 字截断。
- 新增可重复运行的 `scripts/validate_mvp.sh`。

## 关键缺陷修复

1. **跨天快照被永久去重**：旧哈希不包含观察日期，同一商品连续多日不变时后续快照会消失。现按观察日参与哈希。
2. **同日指标变化被误去重**：旧哈希不包含 payload，Star、价格、排名等变化可能丢失。现 payload 参与哈希。
3. **App 版本变化无法识别**：关键 App / instrumentation 版本进入去重语义，并提供 Schema Drift 报告。
4. **aware/naive datetime 比较异常**：外部时间进入数据库前统一规范为 UTC naive。
5. **关键词永久 ACTIVE**：状态改为最近 7/30/90 日证据驱动，旧词可 DECLINING / ARCHIVED。
6. **旧机会永久高分**：Opportunity 只使用最近 90 日证据计算活跃分，旧机会转 DORMANT。
7. **整体热度误当需求增长**：Demand Score 不再直接使用全部 Mention 增长；只有 TREND 类需求证据参与趋势增量。
8. **Probe 语义错配**：GitHub 不再接收招聘/变现 Probe，仅接收 BASE / SUPPLY 类查询。
9. **人工导入伪造 A 级证据**：Generic Import 禁止 OFFICIAL_API / EvidenceQuality.A。
10. **中文候选词硬切**：修复“短剧批量生成与多”等固定长度截断词。

## 自动验证

| 验证项 | 结果 |
|---|---|
| pytest | **15/15 PASS** |
| Python compileall | **PASS** |
| Shell `bash -n` | **PASS** |
| `git diff --check` | **PASS** |
| Alembic SQLite `upgrade head` | **PASS** |
| Alembic `check` | **PASS — No new upgrade operations detected** |
| Alembic SQLite `downgrade base` | **PASS** |
| PostgreSQL Alembic offline DDL generation | **PASS** |
| Fresh DB `/ready` | **PASS** |
| HTTP JSON import | **PASS** |
| Dashboard API | **PASS** |
| Opportunity API | **PASS** |
| Probe Plan API | **PASS** |
| 中文关键词样例烟测 | **PASS** |

## 数据最小化边界

Instrumented App Observation 入库前会：

- 删除常见 token / cookie / authorization / secret / password 字段。
- 删除手机号、邮箱、地址、精确经纬度、IMEI、IMSI、device_id 等常见敏感键。
- 对 title/text 中常见手机号和邮箱进行脱敏。
- URL 仅保留 http/https，删除敏感查询参数和 fragment。

本项目仍不实现认证绕过、验证码绕过、设备风控规避、付费权限绕过或私人数据访问。

## 当前明确未完成

以下不计入本轮 PASS 范围：

- 真实 PostgreSQL 实例 E2E；本轮只完成 SQLite 实迁移和 PostgreSQL 离线 DDL 生成。
- Google Trends 正式 Connector。
- 百度指数 Connector。
- 闲鱼 Web Observation Connector。
- 招聘平台 Connector。
- 抖音指数 / 微信指数 Connector。
- Android 模拟器实际 Hook / Instrumentation 执行 Runtime；当前完成的是安全接入 Contract、Sanitizer 和 Schema Drift。
- LLM 聚类、商业模式抽取和跨主题合并。
- 后台周期调度器；当前 Probe Planner 只生成计划，不自动执行周期任务。

## 运行验收

```bash
./scripts/validate_mvp.sh
./scripts/run_mvp.sh
```

`run_mvp.sh` 会先执行 `alembic upgrade head`，随后仅监听 `127.0.0.1:8000`。
