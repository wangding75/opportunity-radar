# T148 — Batch E: Sources, Source Health, Monitoring Plans, Run Logs and Run Detail (P18–P22)

## Objective

Implement the collection/operations workflow as a batch because source configuration, source health, monitoring plans, and runs are tightly linked and must share the same status vocabulary and navigation.

## Mandatory execution rules

- Repository root: `D:\github\opportunity-radar` unless the actual working directory is already the repository root.
- Read this taskbook, `../dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`, relevant PNGs, and the relevant R02 metadata before editing.
- Do not treat Stitch mock data or labels as backend truth.
- Ordinary build/test/lint/type/API mismatches must be diagnosed and fixed in the same task.
- Missing UI-required backend capability is **not a blocker**: first attempt a minimal safe backend-interface supplement; if that is not safe/possible, register `DEFERRED_UNAVAILABLE`, adapt/hide the UI, and continue.
- Backend supplementation may expose an already-existing business capability, but must not create new business semantics, scoring logic, permission semantics, worker behavior, scheduling meaning, alert meaning, or audit meaning just to satisfy UI.
- Preserve authorization checks and audit requirements on every newly exposed write interface.
- Existing UI visual implementation is deprecated. Do not copy old visual markup/CSS merely to save time. Reusable non-visual API clients, domain types, state/query utilities, validators, and tests may be retained only after review.
- No fake completion: no hardcoded success states, fake API responses in production paths, placeholder buttons wired to no-op handlers, or tests that only assert source strings.
- For every page, implement Loading/Empty/Error/Permission/No Result/Partial states where applicable, not only the happy path.
- Do not push to any remote. Local commits are allowed as task checkpoints; never amend/rebase/squash/force-push during this sequence.
- Final result for each task is exactly `PASS` or `BLOCKED`. `BLOCKED` is reserved for a genuine external blocker that prevents safe repository work; deferred backend gaps are not blockers.


## Scope

Pages P18–P22.

## Required references

- `dependencies/ui_reference_r02/screens/P18_source_management.png`
- `dependencies/ui_reference_r02/screens/P19_source_health.png`
- `dependencies/ui_reference_r02/screens/P20_monitoring_plan.png`
- `dependencies/ui_reference_r02/screens/P21_run_logs.png`
- `dependencies/ui_reference_r02/screens/P22_run_detail.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P18 table and schema-driven Source Editor. Render only fields from actual Source schema; never copy mock Proxy/API-key-rotate/Cron fields from the screenshot or Stitch HTML.
2. Implement P19 health detail using actual health/circuit/failure/run data. Do not provide manual health-state manipulation.
3. Implement P20 Monitoring Plan using actual planner/probe fields. Pause/resume/run-now/schedule edit controls appear only if confirmed.
4. Implement P21 run list and P22 run detail with actual run types/statuses/timing/result/error summary. Do not expose sensitive stack traces.
5. Wire P18/P19/P20/P21/P22 bidirectionally with source/run context and preserve filters where practical.
6. Implement test-connection/save/enable-disable/retry only when T140 confirmed those endpoints. Missing capabilities remain registered and hidden.
7. Test source connection failure, degraded/circuit-open/recovering, run retrying/failure/partial, loading/empty/error.

## Acceptance gates

- [ ] No invented source configuration fields are implemented.
- [ ] Operational statuses map to actual backend values.
- [ ] Run detail never leaks sensitive stack/configuration data.
- [ ] All confirmed source/run actions use real interfaces and authorization.
- [ ] Batch tests pass.

## Required outputs

- `validation/ui_r02/T148_PAGE_REVIEW.md`
- `validation/ui_r02/T148_INTERACTION_TESTS.md`
- `validation/ui_r02/T148_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
