"""Send input to BlueStacks and read its screen.

Usage: python -m core.input tap X Y
       python -m core.input back [escape]
       python -m core.input screenshot [file.png]
"""

import subprocess
import sys

import cv2
import numpy as np

from core.adb import adb, connect

PRESS_DURATION_MS = 100

# Android keycodes for back(). Games differ: some treat Back as "leave the
# app" and close menus on Escape instead, so each game picks its own.
KEYS = {"back": "4", "escape": "111"}


def tap(x, y, duration_ms=PRESS_DURATION_MS):
    # `input tap` has no duration option; a zero-distance swipe holds the press.
    adb("shell", "input", "swipe", str(x), str(y), str(x), str(y), str(duration_ms))


def back(key="back"):
    """Press a back-type key: a name from KEYS or a raw keycode."""
    adb("shell", "input", "keyevent", KEYS.get(key, key))


def capture(retries=10):
    """Return the current BlueStacks screen as PNG bytes.

    BlueStacks' screencap intermittently returns an empty frame (every pixel
    RGBA 0, ~8 KB PNG); those are retried.
    """
    adb_path, serial = connect()
    for _ in range(retries):
        # exec-out (not shell) passes the PNG bytes through unchanged.
        png = subprocess.run([adb_path, "-s", serial, "exec-out", "screencap", "-p"],
                             capture_output=True).stdout
        if not _blank(png):
            return png
    raise RuntimeError(f"BlueStacks returned {retries} blank screenshots in a row")


def _blank(png):
    img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    return img is None or not img.any()


def screenshot(path="screenshot.png"):
    """Save the current BlueStacks screen as a PNG and return the path."""
    with open(path, "wb") as f:
        f.write(capture())
    return path


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    if cmd == "tap" and len(args) == 2:
        x, y = map(int, args)
        tap(x, y)
        print(f"Tapped ({x}, {y})")
    elif cmd == "back" and len(args) <= 1:
        key = args[0] if args else "back"
        back(key)
        print(f"Pressed {key}")
    elif cmd == "screenshot" and len(args) <= 1:
        print(f"Saved {screenshot(*args)}")
    else:
        sys.exit(__doc__)
