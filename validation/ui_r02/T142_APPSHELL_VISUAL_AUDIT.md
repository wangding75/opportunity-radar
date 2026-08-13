# T142 AppShell visual audit

Result: **PASS**

- One `createAppShell()` implementation owns SideNav, TopBar, GlobalContentArea and PageFrame.
- One `NAV_REGISTRY` owns labels, icons, routes, active-state grouping and admin visibility.
- P01 renders outside AppShell; all other route skeletons render through it.
- `P29-A…P29-E` resolve through the same shell and reserve one settings child frame.
- Desktop geometry follows the supplied 240px navigation / 72px topbar / 1440px content guidance.
- Responsive behavior is defined at 900px and 640px breakpoints.
