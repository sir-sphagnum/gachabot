"""Send input to BlueStacks and read its screen.

Usage: python -m core.input tap X Y
       python -m core.input back [escape]
       python -m core.input screenshot [file.png]
"""

import random
import subprocess
import sys
import time

import cv2
import numpy as np

from core.adb import adb, connect

PRESS_MS = (70, 130)      # press length, picked at random per tap
DELAY_S = (0.05, 0.25)    # pause before each tap, picked at random
# Max distance (px) a tap lands from the point asked for, on each axis. The
# smallest button tapped so far is E7's start-screen copyright line, 26 px
# tall: raising this past ~12 can put taps off it.
JITTER_PX = 4

# Android keycodes for back(). Games differ: some treat Back as "leave the
# app" and close menus on Escape instead, so each game picks its own.
KEYS = {"back": "4", "escape": "111"}


def tap(x, y, jitter=JITTER_PX):
    """Tap near (x, y) after a short random pause, with a random press length.
    Returns the (x, y) actually tapped.

    jitter: max offset in px on each axis, normally distributed so most taps
        land close to the point; 0 taps the point exactly.
    """
    x, y = x + _offset(jitter), y + _offset(jitter)
    time.sleep(random.uniform(*DELAY_S))
    # `input tap` has no duration option; a zero-distance swipe holds the press.
    adb("shell", "input", "swipe", str(x), str(y), str(x), str(y),
        str(random.randint(*PRESS_MS)))
    return x, y


def _offset(jitter):
    if not jitter:
        return 0
    return max(-jitter, min(jitter, round(random.gauss(0, jitter / 2))))


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
        print("Tapped ({}, {})".format(*tap(x, y)))
    elif cmd == "back" and len(args) <= 1:
        key = args[0] if args else "back"
        back(key)
        print(f"Pressed {key}")
    elif cmd == "screenshot" and len(args) <= 1:
        print(f"Saved {screenshot(*args)}")
    else:
        sys.exit(__doc__)
