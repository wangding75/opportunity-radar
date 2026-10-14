# T138：建立 GitHub Actions CI Gate

## 目标

让 push / PR 自动执行仓库现有关键验收，防止未测试代码直接进入 main。

## 要求

新增 `.github/workflows/`。

建议分层：

### Job 1：static

- Python compileall
- lint/format（仅执行项目已有工具，不强行引入大型新工具）
- frontend typecheck/build
- false-completion static hygiene
- compose config

### Job 2：unit

- backend pytest unit
- frontend tests（如已有）

### Job 3：postgres-integration

- GitHub Actions PostgreSQL service 或 Docker service
- Alembic fresh migration
- T131/T135 真实 PostgreSQL integration tests

### Job 4：production-smoke

如果可在 Actions 环境可靠执行：

- production compose config
- build
- service health
- API smoke

若 TLS/域名导致完整生产 smoke 无法在 CI 执行，至少完成本地证书/内部网络模式 smoke。

## 约束

1. 不把 secret 写入 workflow。
2. 使用 GitHub Secrets / test-only ephemeral secret。
3. workflow 失败必须真正阻断对应 job。
4. 禁止 `continue-on-error: true` 掩盖关键测试。
5. 对耗时集成测试设置合理 timeout。
6. 固定 Python/Node 版本或从项目配置读取。
7. 缓存不得造成测试结果依赖旧 artifact。

## 验收

至少本地检查 YAML、命令路径和脚本存在性。

如有权限且 push 后 Actions 可运行，必须确认 workflow 实际触发并记录 run 状态。

## Commit

`T138 ci: add repository quality gates`
