# T152 — Cross-Page Interaction, Route-State and Dynamic-Frame Convergence

## Objective

After all batches exist, validate the product as a connected prototype rather than isolated pages. Standardize route params, filter persistence, overlays, breadcrumbs, error transitions, and dynamic child-frame behavior across the full R02 flow.

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

Cross-page convergence; no major new page design.

## Required references

- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_Interaction_Flows.md`
- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_UI_Metadata.json`
- `docs/ui-r02/R02_ROUTE_FRAME_MAP.json`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Walk every flow F01–F07 from the metadata and verify each navigation edge against the actual router and object identifiers.
2. Standardize list->detail->back behavior so filters/pagination/search are preserved where routing architecture supports it.
3. Ensure all drawers/modals open without replacing AppShell or losing the underlying list context; close/cancel/back semantics must be consistent.
4. Ensure tabs/segmented controls and P29 subnavigation refresh only the intended dynamic frame.
5. Validate 401/session-expired, 403, 404, 409/conflict, 429/rate-limit, network error, partial-read failure, and stale states globally.
6. Validate that every UI control marked DEFERRED_UNAVAILABLE is actually omitted/guarded and cannot call a non-existent endpoint.
7. Check responsive/narrow layout behavior for navigation, tables, drawers, graphs and settings frame.
8. Add/extend end-to-end route/interaction tests using the repository-supported browser/test stack. If a full browser runner is unavailable, use the strongest existing integration/smoke method and document the gap; do not mark fake browser coverage.

## Acceptance gates

- [ ] All documented cross-page edges resolve correctly.
- [ ] No dead button/no-op production handler remains.
- [ ] Global error/permission/session states are consistent.
- [ ] Fixed AppShell and SettingsFrame remain visually stable during navigation.
- [ ] Deferred backend gaps cannot produce runtime 404/405 calls.
- [ ] Integration tests pass.

## Required outputs

- `validation/ui_r02/T152_FLOW_COVERAGE.md`
- `validation/ui_r02/T152_DEFERRED_GAP_ENFORCEMENT.md`
- `validation/ui_r02/T152_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
