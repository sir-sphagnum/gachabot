"""Find UI elements in screenshots, crop them, and compare screens. No device access.

Usage: python -m core.vision find [--white] ELEMENT [screen.png] [X Y W H]
           (screen defaults to a live BlueStacks capture)
           --white  match only the white glyphs (text/icons) - for
                    semi-transparent buttons whose background shows through
       python -m core.vision crop screen.png X Y W H out.png

X Y W H are a box in screen pixels (1920x1080): top-left corner, width, height.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

from core import ROOT

# --- template matching ------------------------------------------------------


def find(element, screen, location=None, threshold=0.85, margin=20, white=False):
    """Find the best match of `element` in `screen`, in colour.

    element, screen: file path, PNG bytes, or numpy BGR array. A path relative
        to the repo root (e.g. "e7/templates/start-screen/btn_....png") works
        from any working directory.
    location: optional (x, y, w, h) box in screen coordinates. Only that box,
        padded by `margin` pixels, is searched.
    white: match only the near-white pixels of template and screen (see
        _white). Use for semi-transparent buttons: their white text/icons stay
        the same whatever background shows through, while colour matching
        drifts with it. Crop such templates to the icon, not translucent rims.
    A template PNG with an alpha channel is matched on its opaque pixels only;
    transparent ones are ignored. Use it for text over a changing background:
    keep the letters and their outline opaque, so that whatever shows between
    the letters doesn't count.
    Returns (cx, cy, score): the centre of the match in screen coordinates and
    its score (0..1), or None when the best score is below `threshold`.
    """
    tpl = load(element, templates=True)
    mask = _mask(element)
    img = load(screen)
    if white:
        tpl, img = _white(tpl), _white(img)
    th, tw = tpl.shape[:2]
    H, W = img.shape[:2]

    ox = oy = 0
    if location:
        x0, x1 = _span(location[0], location[2], tw, margin, W)
        y0, y1 = _span(location[1], location[3], th, margin, H)
        img, ox, oy = img[y0:y1, x0:x1], x0, y0

    if img.shape[0] < th or img.shape[1] < tw:
        return None

    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED, mask=mask)
    # Flat regions (e.g. no white pixels at all) give NaN/inf scores.
    res = np.nan_to_num(res, nan=-1.0, posinf=-1.0, neginf=-1.0)
    _, score, _, (mx, my) = cv2.minMaxLoc(res)
    if score < threshold:
        return None
    return ox + mx + tw // 2, oy + my + th // 2, float(score)


def _span(start, length, tpl_len, margin, limit):
    """Pad [start, start+length) by margin, grow it evenly around its centre to
    fit the template, and keep it on screen. Returns (lo, hi)."""
    size = min(limit, max(length + 2 * margin, tpl_len))
    lo = start + length // 2 - size // 2
    lo = max(0, min(lo, limit - size))
    return lo, lo + size


def _white(img, min_value=170, max_saturation=60):
    """Binary image of the near-white pixels: bright and nearly colourless.

    170 sits between the light-grey start-screen icons (~195) and their
    translucent bodies, which stay below ~150 even over a white background.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = (hsv[..., 2] > min_value) & (hsv[..., 1] < max_saturation)
    return mask.astype(np.uint8) * 255


def _mask(src):
    """The opaque pixels (255) of a template PNG with an alpha channel, as a
    single-channel mask; None when it has no alpha (match every pixel)."""
    if not isinstance(src, (str, Path)):
        return None
    path = Path(src)
    if not path.exists() and (ROOT / path).exists():
        path = ROOT / path
    img = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None or img.ndim < 3 or img.shape[2] != 4:
        return None
    return (img[..., 3] > 0).astype(np.uint8) * 255


def load(src, templates=False):
    """Load an image as a BGR array from a path, PNG bytes or an array.
    With templates=True, a path that doesn't exist is also tried under the repo root."""
    if isinstance(src, np.ndarray):
        return src[:, :, :3] if src.ndim == 3 else cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
    if isinstance(src, (bytes, bytearray)):
        img = cv2.imdecode(np.frombuffer(src, np.uint8), cv2.IMREAD_COLOR)
    else:
        path = Path(src)
        if templates and not path.exists() and (ROOT / path).exists():
            path = ROOT / path
        # imdecode handles non-ASCII Windows paths, unlike imread.
        img = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not load image: {src!r}")
    return img


# --- cropping ---------------------------------------------------------------


def crop(screen, x, y, w, h, out):
    """Save the (x, y, w, h) box of `screen` (path, PNG bytes or array) to `out`."""
    img = load(screen)
    H, W = img.shape[:2]
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > W or y + h > H:
        raise ValueError(f"Box {x},{y},{w},{h} is outside the {W}x{H} screen")
    # imencode/tofile handle non-ASCII Windows paths, unlike imwrite.
    ok, png = cv2.imencode(".png", img[y:y + h, x:x + w])
    if not ok:
        raise RuntimeError("PNG encoding failed")
    png.tofile(str(out))
    return out


# --- screen comparison ------------------------------------------------------

TOP_BAR = 20           # pixels to ignore at the top (Pointer location overlay)
SMALL = (192, 108)     # compare at this size so small animations don't count
PIXEL_CHANGE = 25      # a pixel counts as changed if it moved more than this (0-255)


def fingerprint(gray):
    """Shrink a grayscale screenshot down to what we compare."""
    return cv2.resize(gray[TOP_BAR:], SMALL, interpolation=cv2.INTER_AREA)


def difference(a, b):
    """Percent of pixels that changed noticeably (0-100) between two fingerprints.

    Counting strongly changed pixels, rather than averaging the whole screen,
    lets a small popup stand out while background animation stays near 0.
    """
    return 100 * (cv2.absdiff(a, b) > PIXEL_CHANGE).mean()


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    if cmd == "find":
        white = "--white" in args
        args = [a for a in args if a != "--white"]
        if not args:
            sys.exit(__doc__)
        element = args.pop(0)
        screen = args.pop(0) if args and not args[0].lstrip("-").isdigit() else None
        location = tuple(map(int, args)) if len(args) == 4 else None
        if screen is None:
            from core.input import capture
            screen = capture()
        print(find(element, screen, location, white=white))
    elif cmd == "crop" and len(args) == 6:
        x, y, w, h = map(int, args[1:5])
        print(f"Saved {crop(args[0], x, y, w, h, args[5])}")
    else:
        sys.exit(__doc__)
