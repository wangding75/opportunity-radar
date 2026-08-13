"""Docker-runnable HTTP Mock Webhook receiver with explicit MOCK semantics."""

from __future__ import annotations

import json
import os
from threading import Lock

from fastapi import FastAPI, Header, HTTPException, Request

from app.domain.webhook import WebhookEvent, parse_webhook_signature, verify_webhook_signature

MOCK_WEBHOOK_VERSION = "mock-webhook-v1"
MOCK_WEBHOOK_SECRET = os.getenv("MOCK_WEBHOOK_SECRET", "synthetic-webhook-secret-0123456789")


class MockWebhookStore:
    def __init__(self):
        self._lock = Lock()
        self._messages: list[dict] = []

    def receive(self, event: WebhookEvent, *, delivery_id: str, signature: str) -> tuple[dict, bool]:
        with self._lock:
            for message in self._messages:
                if message["delivery_id"] == delivery_id:
                    return message, True
        message = {
            "data_class": "MOCK",
            "event_data_class": event.data_class.value,
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "delivery_id": delivery_id,
            "signature": signature,
            "payload": event.model_dump(mode="json"),
        }
        with self._lock:
            self._messages.append(message)
        return message, False

    def messages(self, limit: int = 100) -> list[dict]:
        with self._lock:
            return list(reversed(self._messages[-limit:]))

    def reset(self) -> None:
        with self._lock:
            self._messages.clear()


app = FastAPI(title="Opportunity Radar Mock Webhook", version=MOCK_WEBHOOK_VERSION)
store = MockWebhookStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": "mock-webhook",
        "data_class": "MOCK",
        "version": MOCK_WEBHOOK_VERSION,
        "signature_verification": "enabled",
        "idempotency": "delivery_id",
    }


@app.post("/v1/hooks")
async def receive(
    request: Request,
    x_webhook_delivery_id: str | None = Header(default=None),
    x_webhook_signature: str | None = Header(default=None),
):
    if not x_webhook_delivery_id or not x_webhook_signature:
        raise HTTPException(status_code=400, detail="mock webhook requires delivery and signature headers")
    body = await request.body()
    try:
        parsed_signature = parse_webhook_signature(x_webhook_signature)
        if parsed_signature.delivery_id != x_webhook_delivery_id:
            raise ValueError("delivery id header does not match signature")
        if not verify_webhook_signature(
            body,
            MOCK_WEBHOOK_SECRET,
            x_webhook_signature,
            expected_delivery_id=x_webhook_delivery_id,
            tolerance_seconds=300,
        ):
            raise ValueError("mock webhook signature verification failed")
        event = WebhookEvent.model_validate(json.loads(body.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="mock webhook received an invalid signed event") from exc
    failure_mode = os.getenv("MOCK_WEBHOOK_FAILURE_MODE", "").strip().lower()
    if failure_mode == "retryable":
        raise HTTPException(status_code=503, detail="MOCK retryable receiver failure")
    if failure_mode == "permanent":
        raise HTTPException(status_code=422, detail="MOCK permanent receiver failure")
    message, duplicate = store.receive(event, delivery_id=x_webhook_delivery_id, signature=x_webhook_signature)
    return {
        "data_class": "MOCK",
        "status": "duplicate" if duplicate else "accepted",
        "receipt_id": f"mock-receipt-{message['delivery_id']}",
        "event_id": message["event_id"],
    }


@app.get("/v1/messages")
def messages(limit: int = 100) -> list[dict]:
    return store.messages(limit=max(1, min(limit, 500)))


@app.post("/v1/reset")
def reset() -> dict[str, str]:
    store.reset()
    return {"status": "reset", "data_class": "MOCK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MOCK_WEBHOOK_PORT", "8083")))
