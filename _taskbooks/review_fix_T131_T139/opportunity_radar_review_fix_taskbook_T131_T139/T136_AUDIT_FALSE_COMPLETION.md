# T136：修复 Functional Audit / False Completion 验收语义

## 背景

当前 `validate_false_completion.py` 主要做静态启发式检查，而 `generate_functional_audit_report.py` 对登记项直接生成 `COMPLETE/PASS`，且允许 `real_data_collected = 0`。

## 目标

避免“静态存在性检查”被解释成“真实功能完整验收”。

## 要求

1. 将现有能力明确拆分：
   - Static Completion Hygiene
   - Runtime Functional Validation
   - Real PostgreSQL Validation
   - External Integration Validation
   - Production Readiness
2. 静态扫描可以继续检查：
   - TODO/FIXME；
   - pass；
   - NotImplementedError；
   - skip；
   - trivial endpoint；
   - 固定 success；
   - 明显 Stub。
3. 静态 Gate 的 PASS 不得自动产生 `coverage.status = COMPLETE`。
4. 功能状态至少支持：
   - NOT_CHECKED
   - STATIC_ONLY
   - TESTED
   - RUNTIME_VERIFIED
   - EXTERNAL_VERIFIED
5. `report_status=PASS` 必须由实际证据计算，禁止固定常量。
6. `real_data_collected=0` 时，不得宣称真实数据链路已经验收。
7. 功能矩阵遗漏项问题必须显式处理：
   - 对路由、worker、connector、核心 service 与矩阵做反向覆盖检查；
   - 未登记的重要功能需报告。
8. 生成报告时附证据来源：
   - test file；
   - runtime report；
   - integration execution；
   - external verification。
9. 更新 README 中所有可能过度表达“complete/pass”的描述。

## 验收

对新的验收脚本写测试，至少证明：

- 只有静态代码时不能得到 `RUNTIME_VERIFIED`；
- real data = 0 时不能得到 external verified；
- 固定 PASS 被移除；
- 未登记核心能力会被报告。

## Commit

`T136 fix: make functional audit evidence based`
