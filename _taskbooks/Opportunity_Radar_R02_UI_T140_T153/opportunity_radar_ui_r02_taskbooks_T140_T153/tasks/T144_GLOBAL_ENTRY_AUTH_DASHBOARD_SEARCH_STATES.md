# T144 — Batch A: Login, Dashboard, Global Search, 403 and 404 (P01–P05)

## Objective

Implement the global-entry batch on top of the frozen AppShell. P01 is unauthenticated; P02–P05 establish the authenticated default, search, permission, and not-found behaviors used by every later batch.

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

Pages P01–P05 only.

## Required references

- `dependencies/ui_reference_r02/screens/P01_login.png`
- `dependencies/ui_reference_r02/screens/P02_dashboard.png`
- `dependencies/ui_reference_r02/screens/P03_global_search.png`
- `dependencies/ui_reference_r02/screens/P04_403_forbidden.png`
- `dependencies/ui_reference_r02/screens/P05_404_not_found.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P01 using existing authentication/session behavior and T140 bindings. Cover invalid credentials, loading, 429/rate-limit, service failure, and successful redirect.
2. Implement P02 Dashboard by composing existing read capabilities. Do not add a backend aggregate endpoint merely for layout convenience if existing reads can safely compose in the client.
3. Implement P03 search using the resolved contract. If no unified search endpoint exists, aggregate existing read endpoints client-side as specified by T140 rather than creating new search semantics.
4. Implement P04 for authenticated permission denial and P05 for route/object not found. Distinguish 401 session expiry, 403, and 404 correctly.
5. Wire AppShell global search entry and user/session transition behavior.
6. Add tests for login success/failure/rate-limit, Dashboard partial load, search result navigation, 403, 404, and session-expiry redirect.
7. Perform visual comparison against all five reference PNGs while preserving shared AppShell geometry.

## Acceptance gates

- [ ] P01–P05 render through the new R02 component system only.
- [ ] 401/403/404 semantics are not conflated.
- [ ] Dashboard partial failures do not blank the whole page.
- [ ] Search does not fabricate backend capability.
- [ ] Visual and interaction tests pass.

## Required outputs

- `validation/ui_r02/T144_PAGE_REVIEW.md`
- `validation/ui_r02/T144_INTERACTION_TESTS.md`
- `validation/ui_r02/T144_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
