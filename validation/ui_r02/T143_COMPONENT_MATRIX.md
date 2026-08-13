# T143 component matrix

| Requirement | Implementation | Reused by |
|---|---|---|
| Button/IconButton | `button`, `iconButton` | all action surfaces |
| Input/Select/Search field | `input`, `select` + field styles | filters/forms |
| Badge/Status | `badge` | list/detail state rows |
| Card/Section | `card` | page sections |
| DataTable | `table` | list pages |
| FilterBar | action-row + field primitives | list pages |
| Pagination | `pagination` | list pages |
| Tabs | `tabs` | settings and segmented sections |
| Loading/Empty/Error/Partial/Stale/Permission/Rate Limit | `statePanel` | all async frames |
| Drawer/Modal/Confirm | `drawer`, `modal` + button variants | contextual detail and destructive confirmation |
| SettingsFrame | `settingsFrame` | P29-A…P29-E |

All primitives are keyboard-usable native controls and have no console-only or no-op click path.
