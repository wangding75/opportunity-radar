# T146 — Batch C: Relationship Graph and Opportunity Workbench (P11–P13)

## Objective

Implement graph exploration and the central Opportunity list/detail workflow. These pages form the core decision workspace and must share stable navigation back to evidence, trends, and sources.

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

Pages P11–P13.

## Required references

- `dependencies/ui_reference_r02/screens/P11_relationship_graph.png`
- `dependencies/ui_reference_r02/screens/P12_opportunity_list.png`
- `dependencies/ui_reference_r02/screens/P13_opportunity_detail.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P11 graph data loading with the project-supported graph/canvas library or existing implementation. Pan/zoom/node selection is UI-only; backend-unsupported filters operate only on returned data.
2. Implement a reusable Node Detail Drawer and deep links to Observation, Trend, Opportunity, and Source.
3. Implement P12 high-density Opportunity table with actual backend fields, conditional actions, filters/sort/pagination per T140.
4. Implement P13 7:3 detail layout with real scoring/evidence/analysis/research fields only. Do not infer scoring dimensions from mock text.
5. Wire P13 to P06/P07, P10, P11, P14, P15/P16, and P17 with correct route params.
6. Hide export/archive/ignore/state actions if T140 did not confirm them.
7. Test graph empty/error, Opportunity analysis states, evidence-partial/stale states, and all deep links.

## Acceptance gates

- [ ] P11–P13 are fully on the new AppShell/common components.
- [ ] No scoring/domain field is invented from PNG mock content.
- [ ] Conditional actions obey resolved capability matrix.
- [ ] Graph and Opportunity navigation round-trips correctly.
- [ ] Visual/interaction tests pass.

## Required outputs

- `validation/ui_r02/T146_PAGE_REVIEW.md`
- `validation/ui_r02/T146_INTERACTION_TESTS.md`
- `validation/ui_r02/T146_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
