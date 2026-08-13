# T147 Interaction Tests

Result: PASS

- P14 analysis status/provider/error/citations are read from the opportunity detail response.
- P15 rows navigate to P16 using real opportunity ids.
- P16 research status, priority, and notes use the confirmed research PATCH endpoint.
- P17 shows persisted citation traceability and evidence links.
- P23 is read-only and exposes no queue mutation, clearing, deletion, or retry button.
- Missing/404 opportunity detail is represented as an object-not-found state.
- API errors, permission errors, session expiry, and empty queue states use shared state handling.
