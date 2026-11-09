# PS3EyeMac v0.6

This handoff preserves the **known-good v0.6 / v0.3 OpenCV capture/display path** and uses a project-local `.venv` so later versions cannot change it.

## Run

```bash
cd ~/Downloads/PS3EyeMac-v0.6-handoff
./run
```

`run-preview.sh` uses only this folder's `.venv`. On first run it installs dependencies locally; later runs reuse them.

## Controls

One compact control window with tabs (drawn in OpenCV so it shares the preview event loop on macOS):

- **Camera**: auto white balance, RGB balance, auto gain, gain, exposure
- **Look**: saturation, contrast, brightness, warmth, tint, gamma
- **Effects**: timestamp with milliseconds, static/noise, VHS

Binary options use on/off switches. Continuous options use clickable sliders. Theme chips support **Plain White**, **Dark Retro**, and **Windows 98**.

`Reset all`, `Save preset`, and `Load preset` sit at the bottom of the control window. Use **Quit** in the control window, or `q`/Esc in either window. Presets save to `camera-preset.json`.

Keyboard shortcuts: `q`/Esc quit, `r` reset, `s` save, `l` load.

`Reset all` restores the exact hardware values captured when the camera opened, resets software grading to neutral, and turns all effects off.

The live preview remains a separate OpenCV window on the known-good capture path.
