#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
TMP_DB="$(mktemp /tmp/opportunity-radar-validate-XXXXXX.db)"
BACKUP_DIR="$(mktemp -d /tmp/opportunity-radar-backup-XXXXXX)"
trap 'rm -f "$TMP_DB"; rm -rf "$BACKUP_DIR"' EXIT

"$ROOT/scripts/build_frontend.sh"
python "$ROOT/scripts/validate_supply_chain.py"
python "$ROOT/scripts/validate_functional_matrix.py"
python "$ROOT/scripts/validate_traceability.py"
python "$ROOT/scripts/scan_functional_matrix_gaps.py"
python "$ROOT/scripts/generate_functional_audit_report.py"
python "$ROOT/scripts/validate_false_completion.py"
python "$ROOT/scripts/validate_false_completion_fixes.py"
python "$ROOT/scripts/validate_false_completion_gate.py"
python "$ROOT/scripts/validate_security_review_auth.py"
python "$ROOT/scripts/validate_security_review_input_http.py"
python "$ROOT/scripts/validate_security_review_keys_logs_config.py"
python "$ROOT/scripts/validate_dependency_supply_chain_review.py"
python "$ROOT/scripts/validate_security_gate.py"
python "$ROOT/scripts/validate_rbac_permission_matrix.py"
python "$ROOT/scripts/generate_api_permission_inventory.py"
python "$ROOT/scripts/validate_api_permission_inventory.py"
python "$ROOT/scripts/validate_frontend_rbac.py"

cd "$BACKEND"
pytest -q
python -m compileall -q app tests "$ROOT/scripts"
bash -n "$ROOT/scripts/run_product.sh" "$ROOT/scripts/run_mvp.sh" "$ROOT/scripts/run_worker.sh" "$ROOT/scripts/run_tests.sh" "$ROOT/scripts/validate_product.sh"
python "$ROOT/scripts/validate_frontend_js.py"
ROOT_FOR_VALIDATION="$ROOT" python - <<'PY'
import os
import yaml
from pathlib import Path
root=Path(os.environ["ROOT_FOR_VALIDATION"])
with (root/'docker-compose.yml').open(encoding='utf-8') as f:
    data=yaml.safe_load(f)
assert {'postgres','migrate','api','worker-collection','worker-analysis','worker-alerts','worker-maintenance'} <= set(data['services'])
for name in ('api','worker-collection','worker-analysis','worker-alerts','worker-maintenance'):
    env=data['services'][name].get('environment', {})
    assert '${POSTGRES_PASSWORD}' not in str(env.get('DATABASE_URL',''))
    assert env.get('PGPASSWORD') == '${POSTGRES_PASSWORD}'
print('DOCKER_COMPOSE_YAML_PASS')
PY

export DATABASE_URL="sqlite:///$TMP_DB"
python -m alembic upgrade head >/dev/null
python "$ROOT/scripts/audit_observation_normalization.py"
python "$ROOT/scripts/audit_keyword_trend_graph.py"
python "$ROOT/scripts/audit_opportunity_score_lineage.py"
python "$ROOT/scripts/audit_alert_replay_backtest.py"
python "$ROOT/scripts/validate_data_correctness_gate.py"
python -m alembic check
python -m alembic downgrade base >/dev/null
python -m alembic upgrade head >/dev/null

DATABASE_URL="postgresql+psycopg://validation:validation@localhost/opportunity_radar" \
  python -m alembic upgrade head --sql >/dev/null

# Historical upgrade checks are independent temporary SQLite databases. Run them
# in parallel so the full validation remains practical without weakening coverage.
upgrade_pids=()
for validator in \
  validate_upgrade_030_to_040.py \
  validate_upgrade_040_to_050.py \
  validate_upgrade_050_to_060.py \
  validate_upgrade_060_to_070.py \
  validate_upgrade_070_to_071.py \
  validate_upgrade_071_to_080.py; do
  python "$ROOT/scripts/$validator" &
  upgrade_pids+=("$!")
done
for pid in "${upgrade_pids[@]}"; do
  wait "$pid"
done

# SQLite backup/restore E2E: restore must recover the pre-mutation database.
python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import settings
engine=create_engine(settings.database_url)
with engine.begin() as c:
    c.execute(text("INSERT INTO seed_keywords (canonical,display_name,enabled,priority,notes,created_at,updated_at) VALUES ('backup-marker','backup-marker',1,3,'before',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
PY
BACKUP_PATH="$(python "$ROOT/scripts/backup_database.py" --output-dir "$BACKUP_DIR" | tail -n 1)"
python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import settings
engine=create_engine(settings.database_url)
with engine.begin() as c:
    c.execute(text("UPDATE seed_keywords SET notes='after' WHERE canonical='backup-marker'"))
PY
python "$ROOT/scripts/restore_database.py" "$BACKUP_PATH" --confirm-restore >/dev/null
python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import settings
engine=create_engine(settings.database_url)
with engine.connect() as c:
    assert c.execute(text("SELECT notes FROM seed_keywords WHERE canonical='backup-marker'" )).scalar_one() == 'before'
print('SQLITE_BACKUP_RESTORE_PASS')
PY

python "$ROOT/scripts/validate_rbac_http.py"

if [[ "${REQUIRE_BROWSER_E2E:-0}" == "1" ]]; then
  python "$ROOT/scripts/validate_browser_e2e.py"
fi

echo "PRODUCT_VALIDATION_PASS"
