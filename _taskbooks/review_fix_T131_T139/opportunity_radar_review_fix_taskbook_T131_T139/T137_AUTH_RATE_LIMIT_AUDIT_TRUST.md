# T137：登录限流与 Audit Actor 信任边界

## Part A：登录限流

### 目标

保留账号失败锁定，同时避免攻击者仅凭用户名持续锁死 OWNER。

### 要求

实现至少两层保护：

1. 账号维度失败计数继续存在；
2. 来源维度限流：
   - IP；
   - 或 IP + username；
   - 必须有明确时间窗口与阈值。

要求：

- production 可配置；
- 不在应用内无限增长内存；
- 多 Worker 下语义一致；
- 优先 PostgreSQL / Redis / 受控反代层，不得只用进程内 dict；
- 响应避免泄漏“用户名是否存在”；
- 增加测试覆盖正常登录、失败、限流恢复、多 Worker/共享存储语义。

## Part B：Audit Actor Header

当前匿名请求可通过客户端 Header 影响 audit actor。

### 要求

1. production 默认不信任客户端提供的 actor header。
2. 已认证用户必须以服务端解析出的 principal 为准。
3. 若确实需要反向代理注入 actor：
   - 显式配置 trusted proxy；
   - 只在可信来源下接受；
   - 文档说明信任边界。
4. 匿名请求使用稳定系统身份，如：
   - `anonymous`
   - `login:<normalized-subject>`（注意不要泄露敏感信息）
5. 增加测试：
   - 普通客户端伪造 X-Actor 不生效；
   - authenticated actor 不可覆盖；
   - trusted proxy 模式若存在则独立验证。

## Commit

`T137 fix: harden login throttling and audit actor trust`
