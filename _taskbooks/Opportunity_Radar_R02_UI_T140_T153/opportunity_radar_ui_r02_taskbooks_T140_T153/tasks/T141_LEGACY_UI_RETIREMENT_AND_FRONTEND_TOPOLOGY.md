# T141 — Retire Existing UI and Define R02 Frontend Topology

## Objective

Treat the current visual UI as deprecated and prepare a clean R02 frontend structure without losing reusable non-visual integration logic. Separate fixed application chrome, route/page frames, shared UI primitives, and dynamic subframes before implementation.

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

Frontend retirement/topology only. No final page styling beyond what is necessary for a compile-safe skeleton.

## Required references

- `dependencies/ui_reference_r02/DESIGN.md`
- `dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`
- `validation/ui_r02/T140_UI_BACKEND_CAPABILITY_MATRIX.json`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Inventory existing frontend files and classify each as PRESENTATION_LEGACY, REUSABLE_NON_VISUAL, ROUTING, API_CLIENT, DOMAIN_TYPE, STATE_QUERY, TEST, BUILD_CONFIG, or ASSET.
2. Deprecate/remove old presentation pages, legacy layout shells, old visual CSS/theme rules, duplicated navigation, and stale presentation assets from the active application path. Do not delete useful API/state/domain logic solely because it lived near old UI files.
3. Ensure no active route imports deprecated visual components or legacy global CSS. Add a temporary compile-safe R02 route skeleton if required.
4. Analyze all 34 prototype pages and define page topology: unauthenticated full-page, AppShell page, list/detail page, settings subframe, drawer/modal overlay, graph/canvas, and read-only diagnostics.
5. Define the fixed-vs-dynamic hierarchy. AppShell must be a single reusable owner of SideNav/TopBar/content viewport; route changes replace only the content frame. P29 A-E must share one SettingsFrame and swap only child content.
6. Define route IDs/params/query-state rules based on actual existing route conventions. Do not change backend routes.
7. Produce a legacy retirement map and an R02 frontend architecture document before T142.

## Acceptance gates

- [ ] No deprecated visual page/layout is active in the runtime route tree.
- [ ] Reusable non-visual code is preserved or deliberately replaced with evidence.
- [ ] Fixed AppShell vs dynamic content-frame boundaries are documented for all pages.
- [ ] P29 is explicitly modeled as one fixed settings frame with five dynamic children.
- [ ] Frontend still builds/tests at the skeleton stage.

## Required outputs

- `validation/ui_r02/T141_LEGACY_UI_RETIREMENT.md`
- `docs/ui-r02/R02_FRONTEND_TOPOLOGY.md`
- `docs/ui-r02/R02_ROUTE_FRAME_MAP.json`
- `validation/ui_r02/T141_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
