# Input, output, SSRF, XML and HTTP security review

`validation/security_review_input_http.json` records eight PASS controls for
request framing, response size, SSRF, redirect/timeout behavior, XML parser
boundaries, provider body validation, output sanitization and fail-closed HTTP
configuration. Its validator requires real code and regression-test targets for
every control and zero live data.

The review confirms that user-controlled Webhook destinations are checked for
credentials, fragments, local/metadata/reserved addresses and unsafe DNS
answers; HTTP adapters do not follow redirects; responses are streamed under a
byte ceiling; and RSS/Trends XML rejects DTD/entity declarations before parsing.
Google Trends now also uses an explicit no-redirect client boundary.

Run it with:

```text
python scripts/validate_security_review_input_http.py
```
