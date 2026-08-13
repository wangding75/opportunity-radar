# R02 shared component contract

`frontend/src/ui.ts` is the single source for common UI primitives. Feature pages receive DOM elements and adapters; they do not create alternate shell, table, status, drawer, modal or settings implementations.

## Components

Button/IconButton, Input, Select, Badge, Card, DataTable, Pagination, statePanel, Drawer, Modal, Tabs and SettingsFrame are available as project-native helpers. `settingsFrame()` owns one fixed SettingsNavigation and one dynamic SettingsChildFrame; only the child element changes when the route changes.

## Async states

Every feature adapter uses one of `loading`, `empty`, `error`, `partial`, `stale`, `permission`, `rate-limit` or `ready`. Errors remain local to the feature frame, preserving AppShell and successful sibling regions.

## Interaction rules

- Buttons are real `<button>` elements with keyboard focus and disabled semantics.
- Links use the centralized hash router and preserve query state.
- Drawers and modals are containers only; mutations stay in feature adapters.
- Tables are dense, horizontally scrollable on narrow layouts, and never contain mock production data.
- Settings P29-A–E share a single frame and navigation instance per render path.
