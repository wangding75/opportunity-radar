# T149 Interaction Tests

Result: PASS

- Alert list loads live event records and handles empty/error states.
- NEW events expose acknowledge; non-NEW events expose resolve.
- Status mutations use `/api/v1/alerts/events/{id}` and preserve server errors.
- Rule creation validates through the backend and reloads the list.
- Rule enable/disable uses the existing patch endpoint.
- No fake notification channel or test-delivery button is rendered.
