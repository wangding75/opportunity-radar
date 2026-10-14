# T150 — Batch G: Audit, Users & Roles, Account & Security (P26–P28)

## Objective

Implement administration/security pages with strict server-authoritative behavior. Audit stays read-only; OWNER invariant remains enforced by backend; token plaintext appears once only after creation.

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

Pages P26–P28.

## Required references

- `dependencies/ui_reference_r02/screens/P26_audit_logs.png`
- `dependencies/ui_reference_r02/screens/P27_users_roles.png`
- `dependencies/ui_reference_r02/screens/P28_account_security.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P26 read-only audit table/filter/detail drawer. Do not add edit/delete/export unless T140 explicitly confirms export.
2. Implement P27 user table/editor using actual roles/statuses. Add risk confirmation for OWNER demotion/disable, but rely on server response for the invariant.
3. On last-owner conflict, keep the drawer open, preserve user input, and show the authoritative server error; never bypass it client-side.
4. Implement P28 password, sessions, API Tokens, logout using actual auth capabilities. Token creation must show plaintext only once in a blocking modal and discard it from UI state after close.
5. Add danger confirmation for token/session revoke only where endpoint exists.
6. Test authorization visibility, audit read-only behavior, OWNER conflict, password failure/success, session expiry, token one-time-secret behavior.

## Acceptance gates

- [ ] Audit has no mutation path.
- [ ] OWNER invariant is server-authoritative.
- [ ] API token plaintext cannot be redisplayed after modal close.
- [ ] RBAC hides inaccessible admin navigation/actions.
- [ ] Batch tests pass.

## Required outputs

- `validation/ui_r02/T150_PAGE_REVIEW.md`
- `validation/ui_r02/T150_SECURITY_INTERACTION_TESTS.md`
- `validation/ui_r02/T150_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
