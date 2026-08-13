#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
python -m alembic upgrade head
exec python -m uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
