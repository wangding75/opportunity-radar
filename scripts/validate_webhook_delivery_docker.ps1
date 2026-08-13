$ErrorActionPreference = "Stop"

# T114-03 acceptance: exercise AlertEvent -> durable Webhook queue -> worker ->
# Compose Mock Webhook. Only SYNTHETIC rows are inserted.
$project = "opportunity-radar-webhook-acceptance"
$env:PORT = "18090"
$env:MOCK_MAIL_HOST_PORT = "18092"
$env:MOCK_WEBHOOK_HOST_PORT = "18093"
$env:WEBHOOK_DELIVERY_ENABLED = "false"
$env:WEBHOOK_ALLOWED_HOSTS = "mock-webhook"
$env:MOCK_WEBHOOK_SECRET = "synthetic-webhook-secret-0123456789"

try {
    docker compose -p $project up -d postgres migrate api mock-webhook
    $ready = Invoke-RestMethod "http://localhost:18090/ready"
    if ($ready.schema_revision -ne "0030_probe_task_leases") {
        throw "unexpected schema revision: $($ready.schema_revision)"
    }
    $mockHealth = Invoke-RestMethod "http://localhost:18093/health"
    if ($mockHealth.data_class -ne "MOCK" -or $mockHealth.signature_verification -ne "enabled" -or $mockHealth.idempotency -ne "delivery_id") {
        throw "mock-webhook health did not report MOCK"
    }

    $sql = @"
INSERT INTO alert_rules (name, enabled, min_score, max_risk_score, min_evidence_count, stages, keyword_contains, cooldown_minutes, created_at, updated_at)
VALUES ('DOCKER_SYNTHETIC_WEBHOOK', true, 0, 100, 1, '[]', '[]', 1440, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET enabled = true, updated_at = NOW();
INSERT INTO alert_events (alert_rule_id, event_key, status, priority, title, message, score, risk_score, created_at)
SELECT id, 'docker-synthetic-webhook-event', 'NEW', 2, 'SYNTHETIC Docker webhook alert', 'SYNTHETIC Docker webhook queue acceptance', 90, 10, NOW()
FROM alert_rules WHERE name = 'DOCKER_SYNTHETIC_WEBHOOK'
ON CONFLICT (event_key) DO UPDATE SET status = 'NEW';
INSERT INTO webhook_endpoints (name, url, secret, secret_fingerprint, event_types, enabled, description, created_at, updated_at)
VALUES ('DOCKER_SYNTHETIC_WEBHOOK_ENDPOINT', 'http://mock-webhook:8083/v1/hooks', 'synthetic-webhook-secret-0123456789', repeat('a', 64), '["alert.event"]', true, 'MOCK acceptance endpoint', NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET enabled = true, url = EXCLUDED.url, updated_at = NOW();
"@
    $sql | docker compose -p $project exec -T postgres psql -U opportunity_radar -d opportunity_radar -v ON_ERROR_STOP=1

    docker compose -p $project run --rm --no-deps `
        -e APP_ENV=development `
        -e AUTH_MODE=disabled `
        -e WEBHOOK_DELIVERY_ENABLED=true `
        worker-alerts python -m app.worker --once --mode alerts --no-sync

    $queue = docker compose -p $project exec -T postgres psql -U opportunity_radar -d opportunity_radar -Atc "SELECT status || '|' || attempt_count FROM webhook_delivery_queue WHERE alert_event_id = (SELECT id FROM alert_events WHERE event_key = 'docker-synthetic-webhook-event');"
    if ($queue.Trim() -ne "SENT|1") {
        throw "unexpected Webhook queue result: $queue"
    }
    $messages = Invoke-RestMethod "http://localhost:18093/v1/messages"
    if ($messages.Count -ne 1 -or $messages[0].data_class -ne "MOCK" -or $messages[0].event_data_class -ne "ALERT_EVENT") {
        throw "expected one MOCK webhook message, got $($messages.Count)"
    }
    Write-Output "PASS: Docker Webhook delivery accepted one SYNTHETIC AlertEvent through queue, worker, and MOCK receiver."
}
finally {
    docker compose -p $project down -v --remove-orphans
}
