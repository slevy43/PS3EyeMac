#!/usr/bin/env python3
"""Check and install all Python dependencies needed by PS3EyeMac."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# import name -> package installed by pip
DEPENDENCIES = [
    ("numpy", "numpy<3"),
    ("Cython", "Cython>=0.29"),
    ("PIL", "Pillow"),
    ("h5py", "h5py"),
    ("cv2", "opencv-python"),
]


def can_import(name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(name)
        return True, None
    except Exception as exc:
        return False, str(exc)


def pip_install(packages: list[str]) -> None:
    if not packages:
        return
    print("[setup] installing missing Python dependencies:")
    for package in packages:
        print(f"        - {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])


def main() -> int:
    missing: list[str] = []
    for module, package in DEPENDENCIES:
        ok, _ = can_import(module)
        if ok:
            print(f"[ok] {module}")
        else:
            print(f"[missing] {module}")
            missing.append(package)

    if missing:
        pip_install(missing)

    # Verify the base dependencies before touching pseyepy. pseyepy imports
    # Pillow/h5py itself, so doing this in two phases gives useful errors.
    failures: list[str] = []
    for module, _package in DEPENDENCIES:
        ok, error = can_import(module)
        if not ok:
            failures.append(f"{module}: {error}")
    if failures:
        print("\nDependency installation failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 2

    ok, error = can_import("pseyepy")
    if not ok:
        print("[missing] pseyepy")
        print("[setup] installing PS3 Eye capture library...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "git+https://github.com/bensondaled/pseyepy.git",
        ])
        ok, error = can_import("pseyepy")
    else:
        print("[ok] pseyepy")

    if not ok:
        print(f"pseyepy still cannot be imported: {error}", file=sys.stderr)
        return 3

    print("[ok] all Python dependencies are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
