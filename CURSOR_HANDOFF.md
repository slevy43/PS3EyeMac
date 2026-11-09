# Cursor handoff — PS3EyeMac v0.6 baseline

This is the known-good baseline for the PS3 Eye on Apple Silicon macOS.

## Preserve these invariants

- `capture/preview.py` uses `pseyepy.Camera` for capture.
- The live preview uses OpenCV (`cv2.imshow` + `cv2.waitKey`). This path is known to work.
- Do not replace the preview/event loop with Tkinter unless deliberately prototyping on a branch.
- Controls live in a second OpenCV-drawn panel (`capture/controls_ui.py`) with Camera / Look / Effects tabs, on/off switches, and themes. Keep both windows on the OpenCV HighGUI loop — do not reintroduce Tkinter beside the preview on macOS.
- Effects already implemented: timestamp with milliseconds, static/noise, VHS.
- Hardware controls already implemented: auto white balance, RGB balance, auto gain, gain, exposure.
- Software look controls already implemented: saturation, contrast, brightness, warmth, tint, gamma.
- `Reset all` restores the camera's startup hardware state, neutral software grading, and effects off.
- Presets save to `camera-preset.json`.
- The `.venv` is local to this project. Do not introduce shared environment pointers between versions.

## Run

```bash
./run
```

On a fresh machine/folder, `run-preview.sh` will call `bootstrap.sh` if the local `.venv` is missing.

## Goal going forward

Iterate from this baseline without changing the proven camera capture/display path unless necessary. Prefer small isolated changes with git commits so regressions can be rolled back immediately.
