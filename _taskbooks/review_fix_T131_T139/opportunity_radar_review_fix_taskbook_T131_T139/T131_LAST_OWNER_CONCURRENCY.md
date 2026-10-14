# T131：修复最后一个 OWNER 并发竞态

## 目标

确保所有并发情况下：

`enabled OWNER >= 1`

当前高风险入口主要在 `backend/app/api/auth.py` 管理员用户修改逻辑。

## 要求

1. 找出所有会减少 enabled OWNER 数量的写入口：
   - OWNER → 非 OWNER；
   - enabled OWNER → disabled；
   - 删除 OWNER；
   - 批量更新或其他等价入口。
2. PostgreSQL 下必须由数据库事务保证并发安全。
3. 推荐 transaction-level advisory lock，或其他可证明跨进程/跨 Worker 生效的数据库锁方案。
4. 禁止仅使用 Python `threading.Lock`。
5. 禁止仅 `SELECT COUNT(...)` 后直接 commit。
6. 获取锁后必须重新读取 OWNER 状态，再判断、再修改。
7. 保持现有合法 API 行为。
8. SQLite 开发环境可保留兼容逻辑，但生产安全保证必须来自 PostgreSQL。

## 必须新增真实并发测试

至少覆盖：

- 2 个 OWNER 同时降级；
- 2 个 OWNER 同时禁用；
- 3 个 OWNER 并发修改；
- 正常单线程合法操作。

验收必须证明最终 `enabled OWNER >= 1`。

真实 PostgreSQL 测试必须使用独立连接/Session/事务。禁止以源码字符串断言代替。

## 验收

```powershell
python -m compileall backend
pytest backend/tests -q
```

如已有 PostgreSQL 专用测试入口，同时执行。

## Commit

`T131 fix: enforce last owner invariant under concurrency`
