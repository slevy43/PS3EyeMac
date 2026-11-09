#!/usr/bin/env python3
"""PS3 Eye preview based on the known-good v0.3 OpenCV capture loop."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from controls_ui import ControlPanel

WINDOW = "PS3 Eye"
ROOT = Path(__file__).resolve().parent.parent
PRESET_PATH = ROOT / "camera-preset.json"

SOFTWARE_DEFAULTS = {
    "Saturation": 100,
    "Contrast": 100,
    "Brightness": 100,
    "Warmth": 100,
    "Tint": 100,
    "Gamma": 100,
}

HARDWARE_SPECS = {
    "Auto WB": ("auto_whitebalance", 1),
    "Red balance": ("red_balance", 255),
    "Green balance": ("green_balance", 255),
    "Blue balance": ("blue_balance", 255),
    "Auto gain": ("auto_gain", 1),
    "Gain": ("gain", 63),
    "Exposure": ("exposure", 255),
}

EFFECT_DEFAULTS = {
    "Timestamp": 0,
    "Static": 0,
    "VHS": 0,
}


def clamp_u8(frame: np.ndarray) -> np.ndarray:
    return np.clip(frame, 0, 255).astype(np.uint8)


def apply_look(frame_rgb: np.ndarray, values: dict[str, int]) -> np.ndarray:
    img = frame_rgb.astype(np.float32)

    contrast = values["Contrast"] / 100.0
    brightness = values["Brightness"] - 100
    img = (img - 127.5) * contrast + 127.5 + brightness

    warmth = (values["Warmth"] - 100) / 100.0
    img[:, :, 0] *= 1.0 + 0.35 * warmth
    img[:, :, 2] *= 1.0 - 0.35 * warmth

    tint = (values["Tint"] - 100) / 100.0
    img[:, :, 0] *= 1.0 + 0.12 * tint
    img[:, :, 2] *= 1.0 + 0.12 * tint
    img[:, :, 1] *= 1.0 - 0.22 * tint
    img = clamp_u8(img)

    saturation = values["Saturation"] / 100.0
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    gamma = max(values["Gamma"], 1) / 100.0
    if abs(gamma - 1.0) > 0.001:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)], dtype=np.uint8)
        img = cv2.LUT(img, table)
    return img


def apply_static(frame_rgb: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    img = frame_rgb.astype(np.int16)
    noise = rng.normal(0, 11, img.shape[:2])[:, :, None]
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    specks = rng.random(img.shape[:2]) < 0.0015
    img[specks] = 255
    return img


def apply_vhs(frame_rgb: np.ndarray, frame_index: int, rng: np.random.Generator) -> np.ndarray:
    img = frame_rgb.copy()
    h, _w = img.shape[:2]

    # subtle chroma separation
    img[:, :, 0] = np.roll(img[:, :, 0], 2, axis=1)
    img[:, :, 2] = np.roll(img[:, :, 2], -2, axis=1)

    # alternating scanlines
    img[1::2] = (img[1::2].astype(np.float32) * 0.84).astype(np.uint8)

    # intermittent horizontal tracking shift
    if frame_index % 19 == 0:
        y = int(rng.integers(0, max(1, h - 24)))
        band_h = int(rng.integers(8, 24))
        shift = int(rng.integers(-14, 15))
        img[y:y + band_h] = np.roll(img[y:y + band_h], shift, axis=1)

    grain = rng.normal(0, 3.5, (img.shape[0], img.shape[1], 1))
    return np.clip(img.astype(np.float32) + grain, 0, 255).astype(np.uint8)


def draw_timestamp(frame_rgb: np.ndarray) -> None:
    now = datetime.now()
    text = now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.52
    thickness = 1
    (width, height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x = max(10, frame_rgb.shape[1] - width - 12)
    y = max(height + 10, frame_rgb.shape[0] - baseline - 12)
    cv2.putText(frame_rgb, text, (x, y), font, scale, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame_rgb, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)


def camera_value(camera, name: str, fallback: int) -> int:
    try:
        return int(getattr(camera, name)[0])
    except Exception:
        return fallback


def set_camera_value(camera, name: str, value: int) -> bool:
    try:
        getattr(camera, name)[0] = int(value)
        return True
    except Exception as exc:
        print(f"warning: could not set {name}={value}: {exc}", file=sys.stderr)
        return False


def read_hardware_defaults(camera) -> dict[str, int]:
    hardware_defaults = {}
    for label, (attr, maximum) in HARDWARE_SPECS.items():
        fallback = 1 if maximum == 1 else (32 if label == "Gain" else 128)
        hardware_defaults[label] = camera_value(camera, attr, fallback)
    return hardware_defaults


def update_hardware(camera, panel: ControlPanel, previous: dict[str, int]) -> None:
    for label, (attr, _maximum) in HARDWARE_SPECS.items():
        value = panel.get(label)
        if previous.get(label) == value:
            continue
        if set_camera_value(camera, attr, value):
            previous[label] = value


def snapshot_settings(panel: ControlPanel) -> dict:
    return {
        "hardware": panel.snapshot_hardware(),
        "software": panel.snapshot_software(),
        "effects": panel.snapshot_effects(),
    }


def save_preset(panel: ControlPanel) -> None:
    PRESET_PATH.write_text(json.dumps(snapshot_settings(panel), indent=2) + "\n")
    print(f"saved preset: {PRESET_PATH}")


def load_preset(panel: ControlPanel, previous_hardware: dict[str, int]) -> None:
    if not PRESET_PATH.exists():
        print(f"no preset found at {PRESET_PATH}")
        return
    try:
        data = json.loads(PRESET_PATH.read_text())
        panel.apply_loaded(data)
        previous_hardware.clear()
        print(f"loaded preset: {PRESET_PATH}")
    except Exception as exc:
        print(f"could not load preset: {exc}", file=sys.stderr)


def reset_all(panel: ControlPanel, previous_hardware: dict[str, int]) -> None:
    panel.reset_to_defaults()
    previous_hardware.clear()
    print("reset all: startup camera state + neutral look + effects off")


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

    if count < 1:
        print("No PS3 Eye detected.", file=sys.stderr)
        return 4

    print(f"Found {count} PS3 Eye camera(s). Opening camera 0 at 640x480 @ 30 fps...")
    print("This build uses the same OpenCV capture/display loop as working v0.3.")
    print("q/esc quit | r reset all | s save | l load")

    camera = None
    panel = None
    frames = 0
    frame_index = 0
    started = time.monotonic()
    rng = np.random.default_rng()

    try:
        camera = Camera(0, fps=30, resolution=Camera.RES_LARGE, colour=True)
        hardware_defaults = read_hardware_defaults(camera)
        previous_hardware = dict(hardware_defaults)

        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW, 960, 720)

        panel = ControlPanel(
            hardware_specs=HARDWARE_SPECS,
            hardware_defaults=hardware_defaults,
            software_defaults=SOFTWARE_DEFAULTS,
            effect_defaults=EFFECT_DEFAULTS,
            on_reset=lambda: reset_all(panel, previous_hardware),
            on_save=lambda: save_preset(panel),
            on_load=lambda: load_preset(panel, previous_hardware),
        )

        while True:
            update_hardware(camera, panel, previous_hardware)

            frame, _timestamp = camera.read()
            if frame is None:
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")) or panel.closed:
                    break
                panel.pump()
                continue

            rgb = apply_look(frame, panel.snapshot_software())
            effects = panel.snapshot_effects()
            if effects["Static"]:
                rgb = apply_static(rgb, rng)
            if effects["VHS"]:
                rgb = apply_vhs(rgb, frame_index, rng)
            if effects["Timestamp"]:
                draw_timestamp(rgb)

            display = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow(WINDOW, display)
            panel.pump()
            frames += 1
            frame_index += 1

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")) or panel.closed:
                break
            if key == ord("r"):
                reset_all(panel, previous_hardware)
            elif key == ord("s"):
                save_preset(panel)
            elif key == ord("l"):
                load_preset(panel, previous_hardware)

            elapsed = time.monotonic() - started
            if elapsed >= 5.0:
                print(f"capture healthy: {frames / elapsed:.1f} displayed fps")
                frames = 0
                started = time.monotonic()

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        return 5
    finally:
        if panel is not None:
            panel.destroy()
        cv2.destroyAllWindows()
        if camera is not None:
            try:
                camera.end()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
