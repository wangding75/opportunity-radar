# T151 — Batch H: Settings Subframes and System Diagnostics (P29A–P29E, P30)

## Objective

Implement the five settings child frames inside one fixed SettingsFrame, then implement read-only system diagnostics. The screenshot fields are placeholders: only real Settings schema/API fields may become writable.

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

Pages P29A–P29E and P30.

## Required references

- `dependencies/ui_reference_r02/screens/P29A_settings_general.png`
- `dependencies/ui_reference_r02/screens/P29B_settings_security.png`
- `dependencies/ui_reference_r02/screens/P29C_settings_notifications.png`
- `dependencies/ui_reference_r02/screens/P29D_settings_integrations.png`
- `dependencies/ui_reference_r02/screens/P29E_settings_source_preference.png`
- `dependencies/ui_reference_r02/screens/P30_system_diagnostics.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement one SettingsFrame with fixed title/environment context/subnavigation and dynamic child route/slot. Switching A-E must not recreate AppShell or duplicate settings navigation.
2. P29A: render only actual general settings fields. Remove any prototype-only display-name/timezone/pagination/logo concepts not present in schema.
3. P29B: deployment-level security settings such as AUTH_MODE, cookie security, trust proxy, database and secrets are read-only/hidden. Only actual writable security settings render.
4. P29C: render actual supported notification channels/config states; secrets never echo.
5. P29D: render only integrations/providers actually present in the repository. Never invent provider URLs or credentials.
6. P29E: render actual Source Preference schema. Restore-default/reorder/weight edits appear only if confirmed.
7. Implement unsaved-change guard at SettingsFrame/child level using UI state, without changing backend transaction semantics.
8. Implement P30 as read-only diagnostics using /health, /ready, and any T140-confirmed diagnostics endpoints. No restart/clear/migrate/delete controls.
9. Test fixed settings frame behavior, dirty-state navigation guard, save conflict/error, secret masking, diagnostics partial failure.

## Acceptance gates

- [ ] P29 A-E share one fixed SettingsFrame and only child content refreshes.
- [ ] No screenshot placeholder becomes a backend setting without schema evidence.
- [ ] Diagnostics is read-only and surfaces partial failures safely.
- [ ] /health and /ready use real endpoints.
- [ ] Batch tests pass.

## Required outputs

- `validation/ui_r02/T151_PAGE_REVIEW.md`
- `validation/ui_r02/T151_SETTINGS_FRAME_TESTS.md`
- `validation/ui_r02/T151_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
