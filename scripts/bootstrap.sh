#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ENV_DIR="$ROOT/.venv"

if "$ROOT/scripts/env.sh" >/dev/null 2>&1; then
  echo "[ok] local environment already ready: $ENV_DIR"
  exit 0
fi

if ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools are required. Run: xcode-select --install"
  exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh"
  exit 1
fi

brew list libusb >/dev/null 2>&1 || brew install libusb
brew list pkg-config >/dev/null 2>&1 || brew install pkg-config

if [[ ! -x "$ENV_DIR/bin/python" ]]; then
  echo "[setup] creating isolated environment at $ENV_DIR"
  python3 -m venv "$ENV_DIR"
fi

"$ENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$ENV_DIR/bin/python" -m pip install 'numpy<3' 'Cython>=0.29' Pillow h5py opencv-python
if ! "$ENV_DIR/bin/python" -c 'import pseyepy' >/dev/null 2>&1; then
  "$ENV_DIR/bin/python" -m pip install 'git+https://github.com/bensondaled/pseyepy.git'
fi

echo "[ok] local setup complete: $ENV_DIR"
