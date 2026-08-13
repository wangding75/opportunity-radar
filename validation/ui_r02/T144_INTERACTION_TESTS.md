# T144 Interaction Tests

Result: PASS

| Case | Expected | Evidence |
|---|---|---|
| Login submit with empty fields | Browser validation prevents request | `required` fields on the new auth form |
| Login 401 | Inline credential error, form becomes usable again | `ApiError.status === 401` branch |
| Login 429 | Rate-limit message | `ApiError.status === 429` branch |
| Login service failure | Service error message | non-401/429 error branch |
| Login success | Fetch `/auth/me`, navigate to P02 | `submitLogin` flow |
| Dashboard API failure | Error state with retry | `renderDashboard` catch path |
| Search query | Parallel live reads and result links to P07/P10/P13 | `runSearch` |
| Search no result | No-result state | empty result branch |
| Search partial failure | Visible partial state plus successful records | `Promise.allSettled` branch |
| 401 during any page | Session transition to P01 | shared `errorState` callback |
| Forbidden recovery | History back or P02 navigation | P04 action row |
| Not-found recovery | History back or P02 navigation | P05 action row |

No production button is wired to a no-op handler.
