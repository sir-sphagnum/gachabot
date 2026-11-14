"""Send input to BlueStacks and read its screen.

Usage: python -m core.input tap X Y
       python -m core.input back [escape]
       python -m core.input screenshot [file.png]
"""

import random
import sys
import time

import cv2
import numpy as np

from core.adb import adb, connect, run_bytes
from core.log import logger, setup
from core.vision import save

log = logger(__file__)

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


def swipe(x1, y1, x2, y2, ms=500):
    """Drag from (x1, y1) to (x2, y2) over `ms` milliseconds (e.g. to scroll
    a list), after a short random pause. A list keeps moving for a moment
    after the drag ends, so callers wait before capturing it."""
    time.sleep(random.uniform(*DELAY_S))
    adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms))


def _offset(jitter):
    if not jitter:
        return 0
    return max(-jitter, min(jitter, round(random.gauss(0, jitter / 2))))


def back(key="back"):
    """Press a back-type key: a name from KEYS or a raw keycode."""
    adb("shell", "input", "keyevent", KEYS.get(key, key))


RGBA_8888 = 1  # screencap's pixel format code for 4 bytes per pixel, R G B A
RETRY_S = 0.5  # pause between screencap retries


def capture(retries=10):
    """Return the current BlueStacks screen as a BGR array (height x width x 3).

    Takes the raw frame (`screencap` without -p): 0.24 s against 0.82 s for a
    PNG, which BlueStacks spends compressing. The raw frame is a header
    (width, height, format as little-endian uint32, then a colour-space field
    on newer Android, so 12 or 16 bytes) followed by the pixels.

    BlueStacks' screencap intermittently returns an empty frame (every pixel
    RGBA 0); those are retried, as are short reads. Empty frames can come in
    bursts longer than `retries` back-to-back reads (seen during an arena
    battle with recon capturing too), so retries are spaced RETRY_S apart.
    Minimising the BlueStacks window doesn't cause them alone: frames stayed
    full over 12 minutes minimised (by its own minimise command and by
    ShowWindow).
    """
    adb_path, serial = connect()
    for attempt in range(retries):
        if attempt:
            time.sleep(RETRY_S)
        # exec-out (not shell) passes the bytes through unchanged.
        raw = run_bytes(adb_path, "-s", serial, "exec-out", "screencap")
        img = _frame(raw)
        if img is not None and img.any():
            return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    raise RuntimeError(f"BlueStacks returned {retries} blank screenshots in a row")


def _frame(raw):
    """The RGBA pixels of a raw screencap, or None if it's short or unreadable."""
    if len(raw) < 12:
        return None
    w, h, fmt = np.frombuffer(raw[:12], "<u4")
    size = int(w) * int(h) * 4
    if fmt != RGBA_8888:
        raise RuntimeError(f"screencap pixel format {fmt}, expected {RGBA_8888} (RGBA_8888)")
    if len(raw) < size + 12:
        return None
    return np.frombuffer(raw[len(raw) - size:], np.uint8).reshape(int(h), int(w), 4)


def screenshot(path="screenshot.png"):
    """Save the current BlueStacks screen as a PNG and return the path."""
    save(capture(), path)
    return path


if __name__ == "__main__":
    setup(console=False)
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    if cmd == "tap" and len(args) == 2:
        x, y = tap(*map(int, args))
        log.debug(f"tap at ({x}, {y})")
        print(f"Tapped ({x}, {y})")
    elif cmd == "back" and len(args) <= 1:
        key = args[0] if args else "back"
        back(key)
        log.debug(f"pressed {key}")
        print(f"Pressed {key}")
    elif cmd == "screenshot" and len(args) <= 1:
        path = screenshot(*args)
        log.debug(f"saved {path}")
        print(f"Saved {path}")
    else:
        sys.exit(__doc__)
