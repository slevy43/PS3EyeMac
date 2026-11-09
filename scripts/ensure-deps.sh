#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "[setup] local Python environment is missing; running bootstrap..."
  exec "$ROOT/scripts/bootstrap.sh"
fi

exec "$ROOT/.venv/bin/python" "$ROOT/scripts/ensure-deps.py"
