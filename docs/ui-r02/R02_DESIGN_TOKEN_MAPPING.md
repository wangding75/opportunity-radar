# R02 design token mapping

Tokens are defined once in `frontend/src/theme.ts` and installed by the single application bootstrap. They are derived from the packaged `DESIGN.md` and keep page-level code from introducing arbitrary global values.

| Design reference | Runtime token |
|---|---|
| `surface/background #f7f9fb` | `--r02-bg`, `--r02-surface-muted` |
| `surface container lowest #ffffff` | `--r02-surface` |
| `primary #2563eb` | `--r02-primary` |
| `primary dark #004ac6` | `--r02-primary-dark` |
| `outline #e2e8f0` | `--r02-outline` |
| `outline active #cbd5e1` | `--r02-outline-strong` |
| status success/warning/error | `--r02-success`, `--r02-warning`, `--r02-danger` and soft fills |
| 4px baseline | `R02_TOKENS.spacing` |
| 8px standard radius | `R02_TOKENS.radius.md` |
| 240px condensed navigation | `R02_TOKENS.layout.navWidth` |
| 1440px desktop content maximum | `R02_TOKENS.layout.maxContent` |
| Inter + Chinese system fallbacks | global `body` font stack |

The shell uses desktop-first 240px navigation, 72px top bar and 32px content gutters. Narrow layouts collapse the navigation to an icon rail, then to a sticky horizontal strip on mobile without changing route or content semantics.
