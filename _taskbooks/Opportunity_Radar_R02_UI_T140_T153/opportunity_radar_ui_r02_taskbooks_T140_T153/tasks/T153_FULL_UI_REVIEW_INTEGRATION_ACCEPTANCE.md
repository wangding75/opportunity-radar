# T153 — Full R02 UI Review, Integration Acceptance and Local Delivery Gate

## Objective

Perform a final, skeptical review of the entire frontend/backend interface integration, visual consistency, code quality, and fake-completion risk. Fix ordinary issues found. End with a local acceptance-ready state and no remote push.

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

Full-program review/fix/acceptance. This is the final task.

## Required references

- `dependencies/ui_reference_r02/PROTOTYPE_AUDIT.md`
- `dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`
- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_Interaction_Flows.md`
- `validation/ui_r02/T140_UI_BACKEND_CAPABILITY_MATRIX.json`

## Execution steps

1. Review the complete git diff from the pre-T140 baseline. Confirm old UI is no longer active and backend changes are limited to minimal interface supplementation.
2. Review every R02 page for common-shell drift: SideNav, TopBar, typography, spacing, card/table density, status badges, PageHeader, drawers, modals, and settings subnavigation.
3. Re-run the final capability matrix against actual routes to detect interface drift introduced during later tasks.
4. Run frontend install/build/typecheck/lint/unit/component/integration tests supported by the repository. Run backend regression for all supplemented interfaces. Fix ordinary failures.
5. Run production/frontend smoke with the real application stack available locally. Exercise login, navigation, key lists/details, source/run flow, opportunity/research flow, alerts, admin, settings, and diagnostics.
6. Perform visual review against all 34 cleaned PNG references. Do not demand pixel-identical mock data; judge shell geometry, hierarchy, component structure, density, spacing, and state coverage.
7. Perform fake-completion audit: search for TODO/no-op handlers, hardcoded success responses, mock production data, unreachable routes, disabled tests, ignored type errors, placeholder buttons, and stale legacy UI imports.
8. Update deferred-gap registry. A deferred capability can remain if safely omitted and documented; it must not be falsely presented as complete.
9. Generate final local acceptance report with commits, tests, changed backend interfaces, deferred gaps, and exact commands to run the app for user review.
10. Ensure worktree is clean after final local commit. Do not push or create remote tags.

## Acceptance gates

- [ ] All 34 pages are implemented or explicitly represented as safe deferred sections according to T140; no fake completion.
- [ ] No active legacy UI remains.
- [ ] AppShell/common UI is singular and consistent.
- [ ] All available tests/builds/smokes pass.
- [ ] No unexpected backend semantic changes exist.
- [ ] Deferred gaps are documented and do not produce broken controls.
- [ ] Final worktree is clean and no remote push occurred.

## Required outputs

- `validation/ui_r02/T153_FINAL_UI_ACCEPTANCE.md`
- `validation/ui_r02/T153_FINAL_CAPABILITY_RECHECK.md`
- `validation/ui_r02/T153_FAKE_COMPLETION_AUDIT.md`
- `validation/ui_r02/T153_FINAL_TEST_REPORT.md`
- `validation/ui_r02/T153_EXECUTION_SUMMARY.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
