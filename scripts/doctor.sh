#!/bin/zsh
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "PS3EyeMac doctor"
echo "================"

echo "macOS: $(sw_vers -productVersion 2>/dev/null || echo unknown)"
echo "arch:  $(uname -m)"
echo

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "[warn] This project is currently aimed at Apple Silicon (arm64)."
else
  echo "[ok] Apple Silicon detected"
fi

echo
echo_usb() { :; }
echo "USB check (looking for Sony PS3 Eye vendor/product IDs 1415:2000)..."
USB_INFO="$(ioreg -p IOUSB -l -w 0 2>/dev/null || true)"

if echo "$USB_INFO" | grep -qiE '0x1415|"idVendor" = 5141'; then
  echo "[ok] Found a USB device with Sony/PS3-Eye vendor ID 0x1415"
  echo "$USB_INFO" | grep -iE -B 6 -A 12 '0x1415|"idVendor" = 5141' | head -n 40
else
  echo "[fail] I could not find vendor ID 0x1415 in the USB tree."
  echo "       Try another hub port, adapter, or connect the camera more directly."
  echo "       Then unplug/replug the Eye and rerun this script."
fi

echo
if command -v brew >/dev/null 2>&1; then
  echo "[ok] Homebrew: $(brew --version | head -n 1)"
else
  echo "[missing] Homebrew"
fi

if command -v python3 >/dev/null 2>&1; then
  echo "[ok] Python: $(python3 --version)"
else
  echo "[missing] python3"
fi

if [[ -f "$ROOT/.venv/bin/python" ]]; then
  echo "[ok] Local capture environment exists"
else
  echo "[info] Local capture environment not created yet"
fi
