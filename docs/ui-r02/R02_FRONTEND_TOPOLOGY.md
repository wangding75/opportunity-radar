# R02 frontend topology

The old runtime was a single `index.html` with inline CSS and one DOM-mutating `main.ts`. T141 removes that visual implementation from the active path while preserving the API client and permission helpers.

## Fixed and dynamic hierarchy

```text
AppShell
├── SideNav                 fixed, permission-filtered registry
├── TopBar                  fixed, search/account/session anchors
└── PageFrame               dynamic route content
    ├── PageHeader          route-owned title/breadcrumb/actions
    ├── DynamicContent      screen implementation
    └── OverlayHost         drawers/modals/toasts
```

Settings uses one fixed child frame rather than five shells:

```text
AppShell → SettingsFrame → SettingsNavigation (fixed) → SettingsChildFrame (P29-A…P29-E)
```

## Page topology

| Screens | Topology |
|---|---|
| P01 | unauthenticated full-page |
| P02–P05, P06, P08–P12, P14–P16, P18, P20–P21, P23–P30 | AppShell + PageFrame |
| P07, P13, P17, P19, P22 | AppShell + detail frame; route identifier in query/path state |
| P11 | AppShell + graph/canvas frame |
| P29-A…P29-E | AppShell + single SettingsFrame + dynamic child |
| Drawer/Modal | OverlayHost owned by AppShell; feature adapters own data mutations |

## Routing contract

The frontend uses hash routes because the backend serves one static entry point. `frontend/src/router.ts` is the sole route registry/parser. Query state remains in the hash query string for filters, cursors, search, sort and return context. Backend API paths are unchanged.

Reusable non-visual code retained after review: `client.ts` (credentials, CSRF, download), `permissions.ts` (RBAC constants and role helpers), TypeScript build configuration. The old presentation markup, inline CSS, duplicated navigation and DOM loader are retired from the active path.
