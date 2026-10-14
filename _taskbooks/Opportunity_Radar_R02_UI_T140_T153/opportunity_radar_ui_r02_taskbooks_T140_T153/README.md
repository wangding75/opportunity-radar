# Opportunity Radar R02 UI Reconstruction Taskbooks — T140–T153

## Strategy

This plan deliberately uses **functional batches**, not 34 independent page tasks and not one giant all-at-once task.

Why:
- Building page-by-page would repeatedly re-create common UI and increase AppShell/navigation drift.
- Building everything in one batch would make interface mismatches and visual regressions hard to isolate.
- The selected sequence freezes the backend/UI contract first, then retires the old UI, then freezes AppShell/common components, then develops tightly coupled page groups.

## Mandatory order

1. T140 — UI ↔ Backend capability audit + minimal interface gap fill
2. T141 — retire legacy UI + frontend topology
3. T142 — AppShell + design tokens
4. T143 — shared components + dynamic frame architecture
5. T144 — P01–P05 global/auth/dashboard/search/error
6. T145 — P06–P10 observation/keyword/trend
7. T146 — P11–P13 graph/opportunity
8. T147 — P14–P17 + P23 analysis/research/queue
9. T148 — P18–P22 source/monitoring/runs
10. T149 — P24–P25 alerts
11. T150 — P26–P28 audit/admin/account security
12. T151 — P29A–E + P30 settings/diagnostics
13. T152 — cross-page interaction/state convergence
14. T153 — full review/integration/fake-completion/final acceptance

## Dependency precedence

`repository truth > T140 resolved matrix > packaged metadata > PNG visual layout > Stitch mock labels/data`

## Important policy changes

- Existing UI is fully deprecated as a visual implementation.
- Minimal backend interface supplementation is allowed and prioritized when it exposes an already-existing business capability required by R02 UI.
- If safe backend supplementation is impossible, record the gap and continue; it does not block the UI program.
- No remote push during this sequence.
