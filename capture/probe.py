#!/usr/bin/env python3
"""Open one PS3 Eye and read a frame, without creating a GUI."""

import sys


def main() -> int:
    try:
        from pseyepy import Camera, cam_count
    except Exception as exc:
        print(f"failed to import pseyepy: {exc}", file=sys.stderr)
        return 2

    try:
        count = cam_count()
    except Exception as exc:
        print(f"camera enumeration failed: {exc}", file=sys.stderr)
        return 3

    print(f"PS3 Eye cameras found: {count}")
    if count < 1:
        print("No camera found. Run ./scripts/doctor.sh and check the USB connection.")
        return 4

    camera = None
    try:
        camera = Camera(0, fps=30, resolution=Camera.RES_LARGE, colour=True)
        frame, timestamp = camera.read()
        if frame is None:
            print("camera opened, but no frame was returned", file=sys.stderr)
            return 5
        print(f"capture ok: shape={frame.shape}, timestamp={timestamp}")
        return 0
    except Exception as exc:
        print(f"camera open/read failed: {exc}", file=sys.stderr)
        return 6
    finally:
        if camera is not None:
            try:
                camera.end()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
