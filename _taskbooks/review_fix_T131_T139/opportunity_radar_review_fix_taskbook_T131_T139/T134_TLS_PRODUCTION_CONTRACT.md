# T134：补齐 HTTPS / Reverse Proxy 生产部署契约

## 背景

production Cookie 使用 Secure 属性，因此生产浏览器访问链路必须走 HTTPS。

## 目标

仓库内形成明确、可执行的生产 HTTPS 部署方案，避免用户直接暴露 `:8000` 后导致认证 Cookie 不工作或不安全。

## 要求

优先采用简单可维护方案，例如 Caddy / Nginx / Traefik 中一种，不要同时引入多套。

至少满足：

1. 浏览器入口为 HTTPS。
2. API `8000` 默认不直接暴露公网。
3. Reverse Proxy 转发必要 Header：
   - Host
   - X-Forwarded-Proto
   - X-Forwarded-For
4. 配置受信代理策略，避免任意客户端伪造 forwarded headers。
5. Secure Session / CSRF Cookie 在生产 HTTPS 下正常工作。
6. 文档明确：
   - 域名要求；
   - 证书方式；
   - 本地测试方式；
   - 哪些端口需要公网开放。
7. 如果自动 ACME 需要真实域名，提供本地自签或 HTTP-only dev override，但 production 不得回退为不安全 Cookie。
8. 不得把真实域名、证书私钥、密码写死入仓库。

## 验收

- 配置语法验证；
- Compose config 验证；
- 可用环境下执行 HTTPS smoke：
  - 登录页/API 可访问；
  - Secure Cookie 正常下发；
  - 登录后请求正常；
  - HTTP 入口跳转 HTTPS 或不可公开访问。

## Commit

`T134 feat: add production https reverse proxy contract`
