# T151 Settings Frame Tests

Result: PASS

- Switching P29-A…P29-E uses the shared settings navigation links.
- AppShell is updated in place by `updateAppShell`; route changes do not create a second shell.
- Each child frame has a clear deferred/read-only reason when no backend schema exists.
- Source preference enable/disable uses the confirmed admin PATCH route only.
- Diagnostics renders each endpoint result independently, so one failed check does not blank the page.
- No secret value is echoed by settings or diagnostics.
