#!/bin/zsh
# Local-only environment. This project never reads or mutates another version's venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$ROOT/.venv"

is_good_env() {
  [[ -x "$ENV_DIR/bin/python" ]] || return 1
  "$ENV_DIR/bin/python" - <<'PY' >/dev/null 2>&1
import numpy, Cython, PIL, h5py, cv2, pseyepy
PY
}

if is_good_env; then
  echo "$ENV_DIR"
  exit 0
fi
exit 1
