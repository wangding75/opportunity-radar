# T132：隔离 production Compose 与 Mock 服务

## 目标

生产拓扑不得无条件依赖：

- mock-mail
- mock-webhook
- mock-enterprise-messaging
- mock-analysis
- 其他仅供开发/测试的 Mock 服务

## 要求

1. 审核：
   - `docker-compose.yml`
   - 其他 compose override
   - `.env*`
   - README / deployment docs
2. `docker-compose.yml` 如定义为 production baseline，应只包含真实生产必要服务。
3. Mock 服务移动到：
   - `docker-compose.dev.yml`
   - `docker-compose.test.yml`
   - 或明确的 `profiles: ["mock"]`
4. 未启用邮件/Webhook 时，API / Worker 不得依赖相关 Mock health。
5. 开发测试环境仍需可一键启动 Mock，不得破坏现有本地联调。
6. production 配置中不得默认把外部通知 URL 指向 localhost Mock。
7. 对 compose 结构补测试或静态校验，证明 production 默认配置不存在 Mock dependency。

## 验收

至少：

```powershell
docker compose config
```

如果 Docker 可用：

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail 200
```

另外验证 dev/test mock profile 或 override 能独立启动。

## Commit

`T132 fix: isolate production compose from mock services`
