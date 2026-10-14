# T133：补齐 API 容器恢复与健康检查

## 目标

API 与 Worker 一样具备生产级生命周期管理。

## 要求

1. API 服务增加：
   - `restart: unless-stopped` 或与项目统一的等价策略；
   - Docker healthcheck。
2. 优先使用现有 `/ready` 作为 readiness。
3. 如果 `/health` 与 `/ready` 语义不同：
   - `/health`：进程存活；
   - `/ready`：数据库/关键依赖就绪。
4. healthcheck 不应依赖宿主机安装 curl。优先使用镜像已有 Python 标准库或明确安装的工具。
5. 合理配置：
   - interval
   - timeout
   - retries
   - start_period
6. 验证数据库暂不可用时 readiness 能失败，恢复后能变 healthy。
7. 验证 API 进程退出后容器可自动恢复。

## 验收

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

若 Docker 可用，实际 kill/restart API 进程或容器，确认自动恢复。

## Commit

`T133 fix: add api healthcheck and restart policy`
