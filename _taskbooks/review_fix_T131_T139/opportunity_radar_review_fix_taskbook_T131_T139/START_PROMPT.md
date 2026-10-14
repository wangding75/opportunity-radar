# Opportunity Radar Review Fix — 总启动指令

工作区：

`D:\github\opportunity-radar`

目标：

一次性修复当前全局代码 Review 已确认的问题，并在真实 PostgreSQL / Docker 能力允许的范围内完成验收。任务按 T131 → T139 顺序执行，不跳号，不并行修改同一业务面。

## 固定执行规则

1. 先读取本目录全部任务书，再开始执行。
2. 每个任务独立完成：
   - 阅读相关源码与现有测试；
   - 修改；
   - 自测；
   - Review diff；
   - Commit；
   - Push；
   - 再进入下一任务。
3. 禁止把多个任务压成一个 Commit。
4. 禁止 `amend`、`rebase`、`squash`、`force push`。
5. 普通代码错误、测试失败、配置错误必须自行修复，不能直接 BLOCKED。
6. 只有外部凭据缺失、Docker/真实 PostgreSQL 完全不可用、破坏性操作需要人工决策等真实外部原因才允许 BLOCKED。
7. 禁止为了“通过测试”删除、绕过、注释或降级现有业务逻辑。
8. 禁止用 Stub、Mock、固定 PASS 文本、源码字符串断言冒充真实运行验证。
9. 测试名称必须与实际证明能力一致。静态 contract test 不得命名为 PostgreSQL E2E / concurrency E2E。
10. 修改任何生产配置时，必须保持本地开发环境可用。
11. 每个任务开始前执行：
    ```powershell
    cd D:\github\opportunity-radar
    git status
    git branch --show-current
    git log -1 --oneline
    ```
12. 每个任务结束前至少执行：
    ```powershell
    git diff --check
    git status
    ```
13. 能运行的现有测试必须运行；不能运行的必须记录精确原因，不得伪造 PASS。
14. T139 为全局最终 Review，不新增业务功能，只修复本轮任务引入的问题和仍然明确存在的 Review 缺陷。
15. 全部完成后工作区必须 clean，远端必须与本地当前分支同步。

## 执行顺序

- T131：最后一个 OWNER 并发不变量
- T132：生产 Compose 与 Mock 服务隔离
- T133：API 容器恢复与健康检查
- T134：HTTPS / Reverse Proxy 生产部署契约
- T135：真实 PostgreSQL 并发与运行时验收
- T136：Functional Audit / False Completion 语义修复
- T137：登录限流与审计 Actor 信任边界
- T138：GitHub Actions CI Gate
- T139：全局回归、虚假完成复查与发布前结论

## 每个任务提交信息

按任务书指定提交信息执行。若必须微调提交说明，可以保留任务编号，例如：

`T131 fix: enforce last owner invariant under concurrency`

## 最终总回执

全部任务完成后仅输出：

```text
PASS
```

或：

```text
BLOCKED
```

PASS 时附：

```text
Start commit:
Final commit:
Branch:
Push status:

T131 commit:
T132 commit:
T133 commit:
T134 commit:
T135 commit:
T136 commit:
T137 commit:
T138 commit:
T139 commit:

Full pytest:
PostgreSQL integration:
Docker production smoke:
CI configuration:
False-completion gate:
Security checks:
Final worktree:
Remaining known issues:
Production readiness:
```

`Production readiness` 只能填写 `READY` 或 `NOT_READY`。

若还有任何未关闭的 P1 / 生产阻断项，必须填写 `NOT_READY`。
