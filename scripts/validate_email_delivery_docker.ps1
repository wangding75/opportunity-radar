$ErrorActionPreference = "Stop"

# T113-05 acceptance: exercise AlertEvent -> queue -> worker -> Compose Mock Mail.
# This uses only synthetic rows and a task-scoped Compose project.
$project = "opportunity-radar-email-acceptance"
$env:PORT = "18080"
$env:MOCK_MAIL_HOST_PORT = "18082"
$env:EMAIL_DELIVERY_ENABLED = "false"
$env:EMAIL_DELIVERY_PROVIDER = "mock"

try {
    docker compose -p $project up -d postgres migrate api worker-alerts mock-mail
    $ready = Invoke-RestMethod "http://localhost:18080/ready"
    if ($ready.schema_revision -ne "0026_email_delivery_queue") {
        throw "unexpected schema revision: $($ready.schema_revision)"
    }
    $mockHealth = Invoke-RestMethod "http://localhost:18082/health"
    if ($mockHealth.data_class -ne "MOCK") {
        throw "mock-mail health did not report MOCK"
    }

    $sql = @"
INSERT INTO alert_rules (name, enabled, min_score, max_risk_score, min_evidence_count, stages, keyword_contains, cooldown_minutes, created_at, updated_at)
VALUES ('DOCKER_SYNTHETIC_EMAIL', true, 0, 100, 1, '[]', '[]', 1440, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET enabled = true, updated_at = NOW();
INSERT INTO alert_events (alert_rule_id, event_key, status, priority, title, message, score, risk_score, created_at)
SELECT id, 'docker-synthetic-email-event', 'NEW', 3, 'SYNTHETIC Docker alert', 'SYNTHETIC Docker queue acceptance', 88, 22, NOW()
FROM alert_rules WHERE name = 'DOCKER_SYNTHETIC_EMAIL'
ON CONFLICT (event_key) DO UPDATE SET status = 'NEW';
"@
    $sql | docker compose -p $project exec -T postgres psql -U opportunity_radar -d opportunity_radar -v ON_ERROR_STOP=1

    docker compose -p $project run --rm --no-deps `
        -e APP_ENV=development `
        -e AUTH_MODE=disabled `
        -e EMAIL_DELIVERY_ENABLED=true `
        -e EMAIL_DELIVERY_PROVIDER=mock_http `
        -e EMAIL_DELIVERY_RECIPIENTS=recipient@example.com `
        -e MOCK_MAIL_URL=http://mock-mail:8082 `
        worker-alerts python -m app.worker --once --mode alerts --no-sync

    $queue = docker compose -p $project exec -T postgres psql -U opportunity_radar -d opportunity_radar -Atc "SELECT status || '|' || attempt_count FROM email_delivery_queue WHERE alert_event_id = (SELECT id FROM alert_events WHERE event_key = 'docker-synthetic-email-event');"
    if ($queue.Trim() -ne "SENT|1") {
        throw "unexpected queue result: $queue"
    }
    $messages = Invoke-RestMethod "http://localhost:18082/v1/messages"
    if ($messages.Count -ne 1 -or $messages[0].data_class -ne "MOCK") {
        throw "expected one MOCK message, got $($messages.Count)"
    }
    Write-Output "PASS: Docker email delivery accepted one SYNTHETIC AlertEvent through queue, worker, and MOCK Mail."
}
finally {
    docker compose -p $project down -v --remove-orphans
}
