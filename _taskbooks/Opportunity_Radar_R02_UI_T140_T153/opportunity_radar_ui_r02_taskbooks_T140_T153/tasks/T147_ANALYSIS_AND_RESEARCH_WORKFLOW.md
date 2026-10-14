# T147 — Batch D: Structured Analysis, Research Workflow, Result and Analysis Queue (P14–P17, P23)

## Objective

Implement the analysis/research chain together because it shares opportunity context, background job state, results, and queue visibility. The UI must distinguish queueing/running/partial/failure from completed evidence-backed results.

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

Pages P14–P17 and P23.

## Required references

- `dependencies/ui_reference_r02/screens/P14_structured_analysis.png`
- `dependencies/ui_reference_r02/screens/P15_research_workflow_list.png`
- `dependencies/ui_reference_r02/screens/P16_research_workflow_detail.png`
- `dependencies/ui_reference_r02/screens/P17_research_result.png`
- `dependencies/ui_reference_r02/screens/P23_analysis_queue.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P14 using actual structured-analysis schema; do not render invented market/risk fields when backend does not provide them.
2. Implement P15 workflow list and P16 workflow detail with real statuses/steps. Unsupported pause/cancel/retry-step/export controls remain hidden.
3. Implement P17 as read-only research result with evidence traceability. Export remains hidden unless T140 confirmed it.
4. Implement P23 queue as an operations/read view using actual queue statuses. Prohibit manual status editing, queue clearing, or job deletion.
5. Wire P13/P14 -> P15/P16 only when existing Research start capability is confirmed; otherwise represent the section as unavailable without blocking the rest of the batch.
6. Wire P23 results/runs back to P14/P22 where actual relationships exist.
7. Add state transition and failure-path tests for queued/running/completed/failed/partial/provider-unavailable/worker-unavailable.

## Acceptance gates

- [ ] P14–P17/P23 use real schemas/statuses only.
- [ ] Unsupported write operations are absent, not no-op.
- [ ] Research result remains traceable to opportunity/evidence.
- [ ] Queue UI is read-only except confirmed safe actions.
- [ ] Batch tests pass even if some capabilities are DEFERRED_UNAVAILABLE.

## Required outputs

- `validation/ui_r02/T147_PAGE_REVIEW.md`
- `validation/ui_r02/T147_INTERACTION_TESTS.md`
- `validation/ui_r02/T147_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
