# T135：真实 PostgreSQL 并发与运行时验收

## 目标

把当前“静态 PostgreSQL contract test”升级为真正的 PostgreSQL 运行时测试，覆盖事务、迁移、多 Worker 和恢复能力。

## 要求

1. 重新检查：
   - `backend/tests/test_postgres_concurrency_contract.py`
   - `scripts/validate_postgres_concurrency.py`
   - `docker-compose.concurrency.yml`
   - Alembic migrations
2. 测试名称必须反映实际能力：
   - 纯源码检查 → contract/static test；
   - 真 PostgreSQL → integration/e2e test。
3. 新增真实 PostgreSQL 测试环境。
4. 至少验证：
   - fresh DB migration up；
   - 应用连接；
   - T131 OWNER 并发；
   - 至少一个队列/任务抢占并发场景；
   - worker 重复竞争不会重复消费；
   - PostgreSQL 重启或连接短暂断开后的恢复；
   - 多 Worker 并发下关键唯一约束与幂等约束有效。
5. 不允许用 SQLite 替代 PostgreSQL E2E。
6. 测试必须可重复执行并清理自身数据。

## 验收

运行真实 PostgreSQL 测试并记录：

- PostgreSQL 版本；
- worker 数；
- 并发次数；
- PASS/FAIL；
- migration revision。

保留静态 contract test 可以，但必须与真实集成测试明确分层。

## Commit

`T135 test: add real postgres runtime concurrency coverage`
