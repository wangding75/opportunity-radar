# T142 — Build AppShell and Global Design-System Foundation

## Objective

Build the fixed visual foundation first so all later pages inherit identical navigation, top bar, spacing, typography, surfaces, and content geometry. This task is the visual anchor for all later R02 work.

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

Only common shell/global styling foundation. Do not implement feature pages beyond shell-hosting placeholders.

## Required references

- `dependencies/ui_reference_r02/DESIGN.md`
- `dependencies/ui_reference_r02/screens/P02_dashboard.png`
- `dependencies/ui_reference_r02/screens/P06_observation_list.png`
- `dependencies/ui_reference_r02/screens/P26_audit_logs.png`
- `docs/ui-r02/R02_FRONTEND_TOPOLOGY.md`

## Execution steps

1. Extract design tokens from DESIGN.md into the project-native theme/token mechanism: colors, typography, spacing, radii, borders, status colors, content max widths, and density rules.
2. Implement a single authenticated AppShell containing SideNav, TopBar, global search entry, account menu anchor, main content viewport, and route outlet/slot.
3. Implement one authoritative navigation registry with labels, icons, routes, active-state resolution, and permission visibility. Do not duplicate nav markup per page.
4. Implement responsive shell behavior for supported desktop/narrow layouts without changing the desktop-first design intent.
5. Build the page-content frame contract: PageHeader, breadcrumb slot, action slot, content region, overlay portal, and loading/error boundary.
6. Ensure P01 Login can render outside AppShell; P04/P05 can reuse AppShell when authenticated.
7. Compare the fixed shell against several reference PNGs and tune dimensions until nav/topbar/content offsets are consistent across all sampled screens.
8. Add component tests for active navigation, permission-hidden navigation, shell rendering, topbar search trigger, and route outlet stability.

## Acceptance gates

- [ ] Exactly one active AppShell implementation owns shared navigation/topbar.
- [ ] No page duplicates SideNav/TopBar markup.
- [ ] Design tokens are centralized; pages do not introduce arbitrary one-off global values.
- [ ] AppShell visual geometry matches the common R02 prototype pattern across sampled screens.
- [ ] Shell tests and frontend build pass.

## Required outputs

- `validation/ui_r02/T142_APPSHELL_VISUAL_AUDIT.md`
- `validation/ui_r02/T142_TEST_REPORT.md`
- `docs/ui-r02/R02_DESIGN_TOKEN_MAPPING.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
