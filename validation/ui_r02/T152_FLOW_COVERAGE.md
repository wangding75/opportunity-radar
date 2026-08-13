# T152 Flow Coverage

Result: PASS

| Flow | Verified route edges |
|---|---|
| F01 entry/auth | `/login` → `/dashboard`; logout → `/login`; 401 redirects to login |
| F02 intelligence | Dashboard → observations/keywords/trends/graph; P06/P08 rows preserve ids into P07/P10 |
| F03 opportunity | P12 → P13 → P14/P16/P17; detail links retain numeric object ids |
| F04 operations | P18 → P19; P20 → P21 → P22; read-only deferred actions omitted |
| F05 alerts | P24 event lifecycle; P25 rule create/toggle; separate page frames |
| F06 administration | P26/P27/P28 under admin navigation; token create/revoke uses server endpoints |
| F07 settings/diagnostics | P29-A…E subnavigation stays inside one SettingsFrame; P30 health/readiness checks are independent |

Cross-page filter context is carried by query parameters for P06/P12 detail links where the source list has a filter. Back/dashboard actions are available on error and not-found states.
