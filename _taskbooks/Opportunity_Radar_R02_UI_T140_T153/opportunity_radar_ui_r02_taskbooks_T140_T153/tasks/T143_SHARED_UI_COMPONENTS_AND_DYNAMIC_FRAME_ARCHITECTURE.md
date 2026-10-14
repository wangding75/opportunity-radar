# T143 — Shared UI Components and Dynamic Subframe Architecture

## Objective

Create the shared component system and dynamic-frame patterns required by the 34 screens before feature batches begin. This prevents every page from reimplementing tables, filters, status badges, drawers, modals, tabs, loading states, and settings subnavigation differently.

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

Shared components and frame architecture only.

## Required references

- `dependencies/ui_reference_r02/DESIGN.md`
- `dependencies/ui_metadata_r02/Opportunity_Radar_R02_UI_Metadata.json`
- `docs/ui-r02/R02_FRONTEND_TOPOLOGY.md`

## Execution steps

1. Implement project-native shared primitives for Button, IconButton, Input, Select, SearchInput, Checkbox/Switch if actually needed, Badge/Status, Card/Section, DataTable, FilterBar, Pagination, Tabs/SegmentedControl, Skeleton, EmptyState, ErrorState, InlineAlert, Toast, Drawer, Modal, ConfirmDialog, Tooltip, CopyButton, and read-only key/value blocks.
2. Build a generic ListFrame and DetailFrame only where they meaningfully eliminate duplication; do not over-abstract feature semantics.
3. Build SettingsFrame for P29 A-E with fixed settings navigation and a dynamic child outlet. Clicking setting tabs must swap only the child frame, not recreate AppShell or the settings navigation.
4. Define overlay behavior: drawers/modals are UI-only containers; data mutation remains in feature adapters.
5. Define asynchronous state conventions for loading, partial failure, empty, no-result, stale, permission-denied, saving, success, validation error, conflict, and rate-limit.
6. Build shared table/query state conventions for URL/query synchronization where supported by existing routing.
7. Add focused component tests and a local component/demo harness only if the repository already supports such a pattern; do not ship a separate product page merely for demos.

## Acceptance gates

- [ ] Feature pages can be built without creating duplicate table/filter/drawer/modal primitives.
- [ ] P29 SettingsFrame proves fixed navigation + dynamic subframe swapping.
- [ ] Async/error states have one consistent presentation contract.
- [ ] Shared components are keyboard/focus usable and do not rely on visual-only click handlers.
- [ ] Frontend build/tests pass.

## Required outputs

- `docs/ui-r02/R02_SHARED_COMPONENT_CONTRACT.md`
- `validation/ui_r02/T143_COMPONENT_MATRIX.md`
- `validation/ui_r02/T143_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
