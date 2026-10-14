# R02 Prototype Dependency Audit

## Result

**PASS WITH REFERENCE CLEANUP**

- Uploaded source ZIP SHA-256: `c25d535a3e0c6ec2e7b9fa426f2870892bbccd982ae2b82958d90369148331b5`
- ZIP entries: **105**
- Valid UI screenshots: **34/34**
- Duplicate screenshot SHA-256: **0**
- Valid design-system document: **1** (`DESIGN.md`)
- Stitch generated `code.html`: **34 files excluded** from development dependencies.

## Why `code.html` is excluded

The HTML exports are not treated as authoritative implementation artifacts. They can include Stitch-generated mock data, speculative fields, concrete provider/channel examples, and interaction controls that are not guaranteed to exist in the repository backend. Using them as source code would create a false-completion/backend-drift risk.

The taskbook therefore keeps:

1. `screen.png` as **visual layout/style references**;
2. `DESIGN.md` as **design-token/style reference**;
3. R02 metadata/interaction files as **interaction intent references**;
4. the actual repository source as the **only authority for backend/API/domain capability**.

## Precedence rule

When references disagree:

`Repository backend/domain truth > T140 resolved UI-backend capability matrix > R02 metadata contract > PNG visual layout > Stitch mock labels/data`

A label/value shown inside a PNG is not proof that the backend supports that field or action.

## Screenshot inventory

| Page | Slug | Clean reference file | Bytes | SHA-256 |
|---|---|---:|---:|---|
| P01 | login | `P01_login.png` | 221147 | `c31c1dfaf2312fe684d96964f13ee7b52dd9c4b708db9f486441e92bb4303297` |
| P02 | dashboard | `P02_dashboard.png` | 379228 | `152d376cf50e8c5983d5a1dd52d86e6b2e7ead1ca5da6af2f59088c5f0d0b705` |
| P03 | global_search | `P03_global_search.png` | 316440 | `7a6f9af6040c3736aedd90cf1691898de407b0a95b0de545942f63de2949798c` |
| P04 | 403_forbidden | `P04_403_forbidden.png` | 157016 | `ec61aecf4e79dbb226f0b782d87795b334306f4e239c171770c91ab73551df2d` |
| P05 | 404_not_found | `P05_404_not_found.png` | 69407 | `41a6a290e8e364780cea665fe83051c8d326f4f9bec6e6a0282fc8fc59802e53` |
| P06 | observation_list | `P06_observation_list.png` | 263848 | `ca9d84dc430e6e78fc4d7827c9feb6b68af5b5281a305feea585f1a2a6e4f36f` |
| P07 | observation_detail | `P07_observation_detail.png` | 449377 | `fb2715f7b87bc62b7b72cf3aba1f00c90368422c11fdbf962804ca1410a370c7` |
| P08 | keyword_discovery | `P08_keyword_discovery.png` | 179367 | `78b2bee0a96c707655018f34294adf4eb87350799d033b74e4b24be3db50eb3b` |
| P09 | watch_keywords | `P09_watch_keywords.png` | 258130 | `f8703747ca2910a0c6a04856d574a2adf7ad6ffbf2f297e005c4041011fcb1ad` |
| P10 | trend_analysis | `P10_trend_analysis.png` | 313299 | `283467e223cd1136d6ed9991b65c40abb9e25fc8c736c1f6b097a721b4d97a08` |
| P11 | relationship_graph | `P11_relationship_graph.png` | 174287 | `23800a0ccbbfa8698d3c6b7e58bb5291cea887cea564f885d30a76122b05dac2` |
| P12 | opportunity_list | `P12_opportunity_list.png` | 256807 | `16e8ca04ff415f1c1c9b4fa7b43806947bbcff403a5d65117bf6217783b59914` |
| P13 | opportunity_detail | `P13_opportunity_detail.png` | 352293 | `615316bdf41903c7ddc07a461aed4b34248a35be00967d164b38fd3274f72148` |
| P14 | structured_analysis | `P14_structured_analysis.png` | 378808 | `225d627939bb215fb3d5e9e2baa1c44711b01b46a705f3b780287b631819beca` |
| P15 | research_workflow_list | `P15_research_workflow_list.png` | 310382 | `81f9cb297b3cea62649aca8a98994fbce993a00826aec89c8237e00eeece8a23` |
| P16 | research_workflow_detail | `P16_research_workflow_detail.png` | 397619 | `007656d9baf2a809beaea1435096082097c9d225e24ca5eff39a8d77910e9a82` |
| P17 | research_result | `P17_research_result.png` | 435736 | `71cd044a99b11fd759bc567224a78fc05b88dbf22dfa36db188362f047d87100` |
| P18 | source_management | `P18_source_management.png` | 226407 | `b96e8f859dce833fc04e559eae347bcc1a496c101cfb7716c7025fd719ad1345` |
| P19 | source_health | `P19_source_health.png` | 112891 | `edf6c53f7d53d9ea4986ac9cbb8531108a98f677a782236dd0c2405195db906d` |
| P20 | monitoring_plan | `P20_monitoring_plan.png` | 149871 | `bf7f5161568533a9def5ff658b789363a473b18070e9b13db5ff06b7ee44dc6b` |
| P21 | run_logs | `P21_run_logs.png` | 265164 | `459db9ae6bc658d79d00673b48cdc2dbc98cb766b2c4cc26c8cd338ec5e0ee1e` |
| P22 | run_detail | `P22_run_detail.png` | 322322 | `56b5571db1a20c54fe2d64b597ae1862ea7b6fb1786bd13c4e1f3dfe48336604` |
| P23 | analysis_queue | `P23_analysis_queue.png` | 256089 | `d598fcd06ee8e0067452cf2c2a2cab7dde924df4fc5b08abde93d2b33c1e5c2d` |
| P24 | alert_inbox | `P24_alert_inbox.png` | 175277 | `8565058322437778c16f65a888c2258d1782908953bc5b2017cb4733a9a2e40f` |
| P25 | alert_rules | `P25_alert_rules.png` | 90850 | `839d368ab1b18e9f0f9ee956478079290da06a2fb87b45f63eaaadc1cd2ecd3e` |
| P26 | audit_logs | `P26_audit_logs.png` | 204138 | `f00871af890653227abb40cb9a0695437965f09eccc09c70d5cefda2bc488938` |
| P27 | users_roles | `P27_users_roles.png` | 128040 | `02b57a2761744304cdd77ba60e3305028b48996398f6510f1d9d91b98b51d87a` |
| P28 | account_security | `P28_account_security.png` | 264885 | `2b491c87e0dae0728acbb2c5ddbc1ebbf1d396384f41c254c79a7aeedbb9dcff` |
| P29A | settings_general | `P29A_settings_general.png` | 212682 | `aebf0cecb0eb0de5dd013d18b4985a5199fd6f73b246e8e5f550c3a7695feae9` |
| P29B | settings_security | `P29B_settings_security.png` | 352245 | `b65eaeaf74f0c3f4e632ccb5a60783b64be59f5188d1bc2aaae72fd79aa55c7e` |
| P29C | settings_notifications | `P29C_settings_notifications.png` | 208975 | `62070b268b7ac69be220f4e6a7cee406f649204e5343302616c559d7cbc8cb79` |
| P29D | settings_integrations | `P29D_settings_integrations.png` | 184202 | `67c27e9d38b8c2978a0afb6d42ee9265fa9451b8fbd099be6af9a32d4ac949d1` |
| P29E | settings_source_preference | `P29E_settings_source_preference.png` | 264940 | `b673d64812af46aafe0d90f06c3c0d9a145fd1c656428693aa80bb539c3fcb9e` |
| P30 | system_diagnostics | `P30_system_diagnostics.png` | 286067 | `5896a2ac020e3eeb450837c3ca502c231d83f6a2cd0bbfff50330a1c32748016` |

## Excluded files

All 34 `code.html` files from the uploaded Stitch export are intentionally omitted from this taskbook package. They are not corrupt; they are **invalid as authoritative development dependencies** under the backend-first verification rule.
