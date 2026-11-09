"""Single themed control panel drawn with OpenCV.

Uses the same HighGUI event loop as the preview window so macOS does not
deadlock between Tk and OpenCV. Preview capture/display stays untouched.
"""
from __future__ import annotations

from typing import Callable

import cv2
import numpy as np

CONTROLS_WINDOW = "PS3 Eye Controls"
WIDTH = 460
HEIGHT = 520

THEMES = {
    "Plain White": {
        "bg": (244, 244, 244),
        "panel": (255, 255, 255),
        "fg": (26, 26, 26),
        "muted": (102, 102, 102),
        "accent": (237, 111, 47),  # BGR
        "border": (208, 208, 208),
        "track": (220, 220, 220),
        "track_on": (237, 111, 47),
        "knob": (255, 255, 255),
        "button": (232, 232, 232),
        "button_border": (180, 180, 180),
        "tab": (234, 234, 234),
        "tab_sel": (255, 255, 255),
        "danger": (60, 60, 200),
    },
    "Dark Retro": {
        "bg": (15, 18, 13),
        "panel": (22, 28, 20),
        "fg": (168, 245, 182),
        "muted": (104, 154, 111),
        "accent": (41, 180, 240),
        "border": (44, 58, 42),
        "track": (40, 48, 36),
        "track_on": (64, 139, 61),
        "knob": (200, 255, 216),
        "button": (30, 40, 28),
        "button_border": (70, 90, 68),
        "tab": (16, 23, 16),
        "tab_sel": (28, 38, 26),
        "danger": (80, 80, 220),
    },
    "Windows 98": {
        "bg": (192, 192, 192),
        "panel": (192, 192, 192),
        "fg": (0, 0, 0),
        "muted": (64, 64, 64),
        "accent": (128, 0, 0),
        "border": (128, 128, 128),
        "track": (128, 128, 128),
        "track_on": (128, 0, 0),
        "knob": (192, 192, 192),
        "button": (192, 192, 192),
        "button_border": (255, 255, 255),
        "tab": (192, 192, 192),
        "tab_sel": (192, 192, 192),
        "danger": (0, 0, 128),
    },
}

TABS = ("Camera", "Look", "Effects")
THEME_NAMES = tuple(THEMES.keys())


def _bgr(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return color


class ControlPanel:
    """One OpenCV window: Camera / Look / Effects + themes + quit."""

    def __init__(
        self,
        hardware_specs: dict,
        hardware_defaults: dict[str, int],
        software_defaults: dict[str, int],
        effect_defaults: dict[str, int],
        on_reset: Callable[[], None],
        on_save: Callable[[], None],
        on_load: Callable[[], None],
        theme_name: str = "Plain White",
    ):
        self.hardware_specs = hardware_specs
        self.hardware_defaults = dict(hardware_defaults)
        self.software_defaults = dict(software_defaults)
        self.effect_defaults = dict(effect_defaults)
        self.on_reset = on_reset
        self.on_save = on_save
        self.on_load = on_load

        self.values: dict[str, int] = {}
        self.maxima: dict[str, int] = {}
        self.kinds: dict[str, str] = {}  # "toggle" | "slider"

        for label, (_attr, maximum) in hardware_specs.items():
            self.values[label] = int(hardware_defaults.get(label, 0))
            self.maxima[label] = int(maximum)
            self.kinds[label] = "toggle" if maximum == 1 else "slider"

        for name, initial in software_defaults.items():
            self.values[name] = int(initial)
            self.maxima[name] = 200
            self.kinds[name] = "slider"

        for name, initial in effect_defaults.items():
            self.values[name] = int(initial)
            self.maxima[name] = 1
            self.kinds[name] = "toggle"

        self.theme_name = theme_name if theme_name in THEMES else "Plain White"
        self.tab = "Camera"
        self.closed = False
        self._drag = None  # (name, x1, x2, max)
        self._hitboxes: list[tuple[str, tuple[int, int, int, int], object]] = []

        cv2.namedWindow(CONTROLS_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(CONTROLS_WINDOW, WIDTH, HEIGHT)
        cv2.setMouseCallback(CONTROLS_WINDOW, self._on_mouse)
        self._canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.render()

    def destroy(self) -> None:
        self.closed = True
        try:
            cv2.destroyWindow(CONTROLS_WINDOW)
        except Exception:
            pass

    def pump(self) -> bool:
        if self.closed:
            return False
        self.render()
        cv2.imshow(CONTROLS_WINDOW, self._canvas)
        return not self.closed

    def request_quit(self) -> None:
        self.closed = True

    def get(self, name: str) -> int:
        return int(self.values[name])

    def set(self, name: str, value: int) -> None:
        if name not in self.values:
            return
        maximum = self.maxima[name]
        self.values[name] = int(max(0, min(maximum, value)))

    def snapshot_hardware(self) -> dict[str, int]:
        return {name: self.get(name) for name in self.hardware_specs}

    def snapshot_software(self) -> dict[str, int]:
        return {name: self.get(name) for name in self.software_defaults}

    def snapshot_effects(self) -> dict[str, int]:
        return {name: self.get(name) for name in self.effect_defaults}

    def reset_to_defaults(self) -> None:
        for name, value in self.hardware_defaults.items():
            self.set(name, value)
        for name, value in self.software_defaults.items():
            self.set(name, value)
        for name, value in self.effect_defaults.items():
            self.set(name, value)

    def apply_loaded(self, data: dict) -> None:
        for name, value in data.get("hardware", {}).items():
            if name in self.hardware_specs:
                self.set(name, value)
        for name, value in data.get("software", {}).items():
            if name in self.software_defaults:
                self.set(name, value)
        for name, value in data.get("effects", {}).items():
            if name in self.effect_defaults:
                self.set(name, value)

    def _theme(self) -> dict:
        return THEMES[self.theme_name]

    def _put(self, img, text, org, color, scale=0.48, thick=1):
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)

    def _rect(self, img, box, color, fill=True, thickness=1):
        x1, y1, x2, y2 = box
        if fill:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), self._theme()["border"], thickness)

    def _add_hit(self, kind: str, box, payload) -> None:
        self._hitboxes.append((kind, box, payload))

    def _controls_for_tab(self) -> list[str]:
        if self.tab == "Camera":
            return list(self.hardware_specs.keys())
        if self.tab == "Look":
            return list(self.software_defaults.keys())
        return list(self.effect_defaults.keys())

    def render(self) -> None:
        t = self._theme()
        img = np.full((HEIGHT, WIDTH, 3), t["bg"], dtype=np.uint8)
        self._hitboxes = []

        # Title + quit
        self._put(img, "PS3 Eye", (14, 28), t["accent"], 0.7, 2)
        quit_box = (WIDTH - 78, 10, WIDTH - 14, 36)
        self._rect(img, quit_box, t["danger"], fill=True)
        self._put(img, "Quit", (WIDTH - 66, 29), (255, 255, 255), 0.5, 1)
        self._add_hit("quit", quit_box, None)

        # Theme chips
        self._put(img, "Theme", (14, 58), t["muted"], 0.42, 1)
        x = 70
        for name in THEME_NAMES:
            label = name if name != "Windows 98" else "Win98"
            tw = 78 if name != "Plain White" else 88
            box = (x, 42, x + tw, 64)
            selected = name == self.theme_name
            self._rect(img, box, t["accent"] if selected else t["button"], fill=True)
            fg = (255, 255, 255) if selected else t["fg"]
            self._put(img, label, (x + 8, 58), fg, 0.38, 1)
            self._add_hit("theme", box, name)
            x += tw + 6

        # Tabs
        tab_y1, tab_y2 = 78, 108
        tab_w = (WIDTH - 28) // len(TABS)
        for i, name in enumerate(TABS):
            x1 = 14 + i * tab_w
            x2 = x1 + tab_w - 4
            box = (x1, tab_y1, x2, tab_y2)
            selected = name == self.tab
            self._rect(img, box, t["tab_sel"] if selected else t["tab"], fill=True, thickness=2 if selected else 1)
            self._put(img, name, (x1 + 18, tab_y1 + 21), t["fg"] if selected else t["muted"], 0.5, 1)
            self._add_hit("tab", box, name)

        # Body panel
        body = (14, 118, WIDTH - 14, HEIGHT - 70)
        self._rect(img, body, t["panel"], fill=True)

        y = 140
        for name in self._controls_for_tab():
            if self.kinds[name] == "toggle":
                y = self._draw_toggle(img, name, y)
            else:
                y = self._draw_slider(img, name, y)
            y += 8

        # Action buttons
        actions = (
            ("Reset all", self.on_reset),
            ("Save preset", self.on_save),
            ("Load preset", self.on_load),
        )
        bx = 14
        for label, _cb in actions:
            box = (bx, HEIGHT - 48, bx + 130, HEIGHT - 16)
            self._rect(img, box, t["button"], fill=True, thickness=2)
            self._put(img, label, (bx + 16, HEIGHT - 26), t["fg"], 0.45, 1)
            self._add_hit("action", box, label)
            bx += 140

        self._canvas = img

    def _draw_toggle(self, img, name: str, y: int) -> int:
        t = self._theme()
        self._put(img, name, (28, y + 16), t["fg"], 0.48, 1)
        on = bool(self.values[name])
        box = (WIDTH - 86, y, WIDTH - 28, y + 24)
        self._rect(img, box, t["track_on"] if on else t["track"], fill=True)
        knob_x = box[2] - 14 if on else box[0] + 14
        cv2.circle(img, (knob_x, y + 12), 9, t["knob"], -1)
        cv2.circle(img, (knob_x, y + 12), 9, t["border"], 1)
        self._put(img, "On" if on else "Off", (WIDTH - 130, y + 16), t["muted"], 0.4, 1)
        self._add_hit("toggle", box, name)
        return y + 30

    def _draw_slider(self, img, name: str, y: int) -> int:
        t = self._theme()
        value = self.values[name]
        maximum = max(1, self.maxima[name])
        self._put(img, name, (28, y + 14), t["fg"], 0.45, 1)
        self._put(img, str(value), (WIDTH - 52, y + 14), t["muted"], 0.45, 1)

        track = (28, y + 24, WIDTH - 28, y + 36)
        self._rect(img, track, t["track"], fill=True)
        ratio = value / maximum
        filled_x = int(track[0] + (track[2] - track[0]) * ratio)
        if filled_x > track[0]:
            self._rect(img, (track[0], track[1], filled_x, track[3]), t["accent"], fill=True)
        cv2.circle(img, (filled_x, (track[1] + track[3]) // 2), 7, t["knob"], -1)
        cv2.circle(img, (filled_x, (track[1] + track[3]) // 2), 7, t["accent"], 1)
        self._add_hit("slider", track, (name, track[0], track[2], maximum))
        return y + 46

    def _hit_test(self, x: int, y: int):
        for kind, box, payload in reversed(self._hitboxes):
            x1, y1, x2, y2 = box
            if x1 <= x <= x2 and y1 <= y <= y2:
                return kind, payload, box
        return None, None, None

    def _set_slider_from_x(self, name: str, x1: int, x2: int, maximum: int, x: int) -> None:
        if x2 <= x1:
            return
        ratio = (x - x1) / float(x2 - x1)
        self.set(name, int(round(max(0.0, min(1.0, ratio)) * maximum)))

    def _on_mouse(self, event, x, y, flags, _param) -> None:
        if self.closed:
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            kind, payload, _box = self._hit_test(x, y)
            if kind == "quit":
                self.request_quit()
            elif kind == "theme":
                self.theme_name = payload
            elif kind == "tab":
                self.tab = payload
            elif kind == "toggle":
                self.values[payload] = 0 if self.values[payload] else 1
            elif kind == "slider":
                name, x1, x2, maximum = payload
                self._drag = payload
                self._set_slider_from_x(name, x1, x2, maximum, x)
            elif kind == "action":
                if payload == "Reset all":
                    self.on_reset()
                elif payload == "Save preset":
                    self.on_save()
                elif payload == "Load preset":
                    self.on_load()

        elif event == cv2.EVENT_MOUSEMOVE and self._drag is not None and (flags & cv2.EVENT_FLAG_LBUTTON):
            name, x1, x2, maximum = self._drag
            self._set_slider_from_x(name, x1, x2, maximum, x)

        elif event == cv2.EVENT_LBUTTONUP:
            self._drag = None
