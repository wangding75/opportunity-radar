#!/usr/bin/env bash
set -euo pipefail
echo "validate_mvp.sh is deprecated; forwarding to validate_product.sh" >&2
exec "$(dirname "$0")/validate_product.sh" "$@"
