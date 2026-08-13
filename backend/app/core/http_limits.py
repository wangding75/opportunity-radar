from __future__ import annotations

import httpx


def read_limited_response(response: httpx.Response, *, max_bytes: int, label: str) -> bytes:
    """Read a streaming HTTP response with a hard byte ceiling.

    Callers must obtain the response through ``client.stream``. Content-Length is
    checked before reading when available, and chunked responses are bounded while
    iterating so the safety limit is effective rather than a post-download check.
    """
    raw_length = response.headers.get("Content-Length")
    if raw_length:
        try:
            content_length = int(raw_length)
        except ValueError:
            content_length = None
        if content_length is not None and content_length > max_bytes:
            raise ValueError(f"{label} exceeded configured size limit")

    body = bytearray()
    for chunk in response.iter_bytes():
        if not chunk:
            continue
        if len(body) + len(chunk) > max_bytes:
            raise ValueError(f"{label} exceeded configured size limit")
        body.extend(chunk)
    return bytes(body)
