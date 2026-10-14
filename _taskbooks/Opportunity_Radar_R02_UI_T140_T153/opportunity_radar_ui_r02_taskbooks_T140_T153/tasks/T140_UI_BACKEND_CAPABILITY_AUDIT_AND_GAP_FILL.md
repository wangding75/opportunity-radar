# T140 — R02 UI ↔ Backend Capability Audit and Minimal Gap Fill

## Objective

Before any R02 UI development, establish the real contract between all 34 prototype screens and the current repository backend. Every required read/write/navigation capability must be classified. When the underlying business capability already exists but the frontend cannot access it because an API/interface/response field is missing, add the smallest safe backend interface first. When safe supplementation is impossible, record the gap and continue; the gap must not block later UI tasks.

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

Backend/interface audit and minimal interface supplementation only. **Do not start visual R02 page development in this task.**

## Required references

- `dependencies/ui_reference_r02/PROTOTYPE_AUDIT.md`
- `dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`
- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_UI_Metadata.json`
- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_Interaction_Flows.md`

## Execution steps

1. Confirm branch/HEAD/worktree and record the baseline. Do not rewrite history or push.
2. Inventory all current backend API routes, request/response schemas, auth/permission guards, service-layer capabilities, queue/worker capabilities, settings/source-preference/alert/research capabilities, and diagnostics endpoints. Inventory frontend API clients/hooks/types separately.
3. For every R02 page and every action in the metadata JSON, build a row in a capability matrix with: page, control/action, intended behavior, actual route/method/schema, permission, status, evidence file:line, frontend handling, and notes.
4. Classify each row as one of: MATCHED, UI_ONLY, MINIMAL_BACKEND_SUPPLEMENT, DEFERRED_UNAVAILABLE, FORBIDDEN_DOMAIN_EXPANSION.
5. For MINIMAL_BACKEND_SUPPLEMENT rows, verify that the underlying business/service capability already exists. Add only the minimum endpoint/response exposure needed. Reuse current domain/service logic; do not fork behavior into route handlers.
6. For each supplemented backend interface, add request validation, authorization, audit behavior where appropriate, error mapping, unit/integration tests, and update API client/types if the repository owns them.
7. For capabilities that cannot be safely supplemented, write them to `validation/ui_r02/T140_DEFERRED_UI_BACKEND_GAPS.md` and JSON. Define exact UI behavior: HIDE, READ_ONLY, DISABLED_WITH_REASON, or DEFERRED_PAGE_SECTION. Continue execution.
8. Resolve exact API method/path bindings in a generated implementation contract. Replace VERIFY_LATEST only in the generated resolved copy; do not alter the packaged dependency metadata.
9. Run backend tests relevant to every supplemented interface plus existing auth/RBAC/audit regression tests. Fix ordinary failures.
10. Produce a final audit summary with counts by status and a zero-ambiguity list of capabilities still deferred.

## Acceptance gates

- [ ] All 34 screens/actions have matrix coverage; no unmapped actionable control remains.
- [ ] Every newly added endpoint only exposes existing business capability and has tests.
- [ ] No backend business semantics were invented to satisfy a screenshot.
- [ ] Deferred gaps are registered with concrete UI fallback and do not block T141.
- [ ] Backend regression suite for touched areas passes.
- [ ] Working tree contains only intentional T140 changes before commit.

## Required outputs

- `validation/ui_r02/T140_UI_BACKEND_CAPABILITY_MATRIX.md`
- `validation/ui_r02/T140_UI_BACKEND_CAPABILITY_MATRIX.json`
- `validation/ui_r02/T140_DEFERRED_UI_BACKEND_GAPS.md`
- `validation/ui_r02/T140_DEFERRED_UI_BACKEND_GAPS.json`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`
- `validation/ui_r02/T140_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
