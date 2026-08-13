#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$ROOT/backend/app/static/js"
mkdir -p "$ROOT/backend/app/static/js"
tsc -p "$ROOT/frontend/tsconfig.json"
echo FRONTEND_TS_BUILD_PASS
