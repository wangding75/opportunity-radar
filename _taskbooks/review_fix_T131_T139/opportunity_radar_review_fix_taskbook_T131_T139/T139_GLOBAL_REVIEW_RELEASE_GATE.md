# T139：全局回归、虚假完成复查与发布前结论

## 目标

对 T131-T138 修改后的仓库做一次完整 Review，不新增业务需求，只验证是否真正解决本轮问题。

## Review 范围

重点重新检查：

1. OWNER 最后管理员并发不变量；
2. production Compose 是否还依赖 Mock；
3. API restart / healthcheck；
4. HTTPS / Secure Cookie 生产链路；
5. PostgreSQL 真并发是否真实执行；
6. Functional Audit 是否仍存在固定 PASS / COMPLETE；
7. 登录限流是否可被简单绕过；
8. X-Actor / forwarded header 信任边界；
9. CI 是否真正执行关键 Gate；
10. 新代码是否引入：
    - TODO/FIXME；
    - pass；
    - NotImplementedError；
    - skip；
    - 假 E2E；
    - 固定成功；
    - 测试仅检查源码字符串；
    - 大量异常吞掉；
    - 无上限重试；
    - 明文 secret；
    - 容器 root / 过度权限等明显部署风险。

## 全量验收

至少：

```powershell
cd D:\github\opportunity-radar

python -m compileall backend
pytest backend/tests -q

git diff --check
git status
```

同时运行仓库已有：

- frontend build/typecheck/test；
- functional audit；
- false-completion scan；
- SBOM / supply-chain validation；
- compose config；
- PostgreSQL integration；
- production Docker smoke。

如果 Docker 可用，至少执行一次：

```powershell
docker compose down -v
docker compose up -d --build
docker compose ps
```

并验证：

- fresh DB；
- migration；
- API healthy；
- login；
- 至少一个核心业务 API；
- worker；
- restart recovery；
- Mock 未进入 production 默认拓扑。

## 生产结论规则

只有以下全部成立才能给 `Production readiness: READY`：

- 无未关闭 P1；
- 无已知 last-owner race；
- production 默认无 Mock dependency；
- HTTPS 契约完整；
- PostgreSQL 真测试 PASS；
- API / Worker 自恢复验证 PASS；
- CI 已建立；
- false-completion 报告不再夸大；
- 全量测试 PASS；
- 没有通过跳过/Stub/固定结果规避验收。

否则必须：

`Production readiness: NOT_READY`

并列出剩余阻断项。

## Commit

如果只做 Review、无代码变化，不创建空 Commit。

若发现本轮引入的小缺陷并修复：

`T139 fix: close global review findings`

最终 push 后确认：

```powershell
git status
git log --oneline -10
```
