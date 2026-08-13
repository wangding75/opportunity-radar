#!/usr/bin/env bash
set -euo pipefail
echo "run_mvp.sh is deprecated; forwarding to run_product.sh" >&2
exec "$(dirname "$0")/run_product.sh" "$@"
