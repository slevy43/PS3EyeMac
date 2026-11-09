#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ENV_DIR="$($ROOT/scripts/env.sh 2>/dev/null)"; then
  echo "[ok] using existing environment: $ENV_DIR"
else
  "$ROOT/scripts/bootstrap.sh"
  ENV_DIR="$($ROOT/scripts/env.sh)"
fi

exec "$ENV_DIR/bin/python" "$ROOT/capture/preview.py"
