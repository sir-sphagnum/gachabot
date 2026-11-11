"""Tap a UI element until an expected element shows up, closing popups on the way.

Usage: python -m core.nav BUTTON EXPECTED [EXPECTED ...] [--delay S] [--tries N]
                          [--no-popups]

Games sometimes swallow a tap (e.g. a popup that ignores input while it is
still animating in). tap_until taps BUTTON, then keeps checking the screen for
EXPECTED for `delay` seconds; if it hasn't appeared, it taps again, up to
`tries` taps. It stops as soon as any EXPECTED element is on screen, including
before the first tap.

Before each tap it also looks for the game's known popups
(<game>/templates/common/popups/, see core/tree.py). If one is open, it taps that
popup's close button until the popup is gone, then carries on. Closing a popup
doesn't use up one of the `tries`.

BUTTON is a template file or an X,Y point (e.g. 1869,49); EXPECTED are
template files. Template names that follow the map skill's scheme
(btn_/info_..._X-Y-W-H[_white].png) are searched only in their box, matching
white-only when the name says so; any other file is searched over the whole
screen. Exits 0 when an expected element was seen, 1 otherwise.
"""

import argparse
import sys
from functools import cache
from pathlib import Path

from core import ROOT
from core.device import wait_until
from core.input import capture, tap
from core.tree import ELEMENT, load_popups
from core.vision import find


def tap_until(button, expected, delay=1.5, tries=5, popups=True, verbose=False):
    """Tap `button` until one of `expected` is on screen.

    button: template path of the element to tap, or an (x, y) point. A
        template is located on the live screen before each tap, so the tap
        lands on the match, not the stored box; if it isn't on screen, that
        round taps nothing and just waits. A point is tapped as is (e.g. an
        empty spot of a lobby, to wake its HUD).
    expected: template path, or a list of them; stop when any one is found.
    delay: seconds to keep checking for `expected` after each tap before
        tapping again.
    tries: maximum number of taps on `button`.
    popups: which popups to close before tapping. True: the popups of the
        game the templates live in (<game>/templates/...). A game name: that
        game's popups. A dict from core.tree.load_popups. False/None: none.
    Returns (template, (cx, cy, score)) for the expected element that was
    found, or None if it never appeared (or a popup couldn't be closed).
    """
    if isinstance(button, (list, tuple)):
        button = tuple(int(v) for v in button)  # accept [x, y] as well as (x, y)
    if isinstance(expected, (str, Path)):
        expected = [expected]
    say = print if verbose else (lambda *a: None)
    known = _resolve_popups(popups, [button, *expected])

    taps = closed = 0
    while taps < tries:
        screen = capture()
        hit = _first(expected, screen)
        if hit:
            return hit

        popup = open_popup(known, screen)
        if popup and closed < tries:
            closed += 1
            say(f"Popup {popup} is open; closing it")
            if not close_popup(known[popup], delay, tries, say):
                say(f"Couldn't close popup {popup}")
                return None
            continue

        taps += 1
        _tap(button, screen, f"Tap {taps}/{tries}", say)
        hit = _wait_for(lambda s: _first(expected, s), delay)
        if hit:
            return hit

    return _first(expected, capture())


def open_popup(popups, screen):
    """Name of the first popup in `popups` that is open on `screen`, or None.
    A popup is open when all of its info_ images match."""
    for name, popup in popups.items():
        if _is_open(popup, screen):
            return name
    return None


def close_popup(popup, delay=1.5, tries=5, say=lambda *a: None):
    """Tap `popup`'s close button until the popup is gone. Returns True once
    it is gone, False if it is still open after `tries` taps."""
    for attempt in range(1, tries + 1):
        screen = capture()
        if not _is_open(popup, screen):
            return True
        _tap(popup["close"]["file"], screen, f"  close tap {attempt}/{tries}", say)
        if _wait_for(lambda s: not _is_open(popup, s), delay):
            return True
    return not _is_open(popup, capture())


def _tap(button, screen, label, say):
    match = (*button, 1.0) if isinstance(button, tuple) else locate(button, screen)
    if match:
        cx, cy, _ = match
        tap(cx, cy)
        say(f"{label} at ({cx}, {cy})")
    else:
        say(f"{label} skipped: {Path(button).name} not on screen")


def _wait_for(check, delay):
    """Keep capturing until check(screen) is truthy or `delay` seconds pass.
    Returns the truthy result, or None."""
    return wait_until(lambda: check(capture()), delay, interval=0)


def _is_open(popup, screen):
    return bool(popup["info"]) and all(
        find(i["file"], screen, i["box"], white=i["white"]) for i in popup["info"])


def _resolve_popups(popups, templates):
    if not popups:
        return {}
    if isinstance(popups, dict):
        return popups
    if isinstance(popups, str):
        return _game_popups(popups)
    for t in templates:  # popups=True: infer the game from the template paths
        if isinstance(t, tuple):
            continue
        try:
            parts = Path(t).resolve().relative_to(ROOT).parts
        except ValueError:
            continue
        if len(parts) > 1 and parts[1] == "templates":
            return _game_popups(parts[0])
    return {}


@cache
def _game_popups(game):
    return {n: p for n, p in load_popups(game)[0].items() if p["info"] and p["close"]}


def _first(templates, screen):
    for t in templates:
        match = locate(t, screen)
        if match:
            return str(t), match
    return None


def locate(template, screen):
    """Find `template` on `screen` like core.vision.find, but for map-scheme names
    (btn_/info_..._X-Y-W-H[_white].png) search only their box, white-only when
    the name says so. Returns (cx, cy, score) or None."""
    m = ELEMENT.match(Path(template).name)
    if not m:
        return find(template, screen)
    box = tuple(int(m[k]) for k in "xywh")
    return find(template, screen, box, white=bool(m["white"]))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("button")
    p.add_argument("expected", nargs="+")
    p.add_argument("--delay", type=float, default=1.5,
                   help="seconds to wait for EXPECTED after each tap (default 1.5)")
    p.add_argument("--tries", type=int, default=5, help="maximum taps (default 5)")
    p.add_argument("--no-popups", action="store_true", help="don't look for popups")
    a = p.parse_args()
    if "," in a.button and not Path(a.button).exists():
        a.button = tuple(int(v) for v in a.button.split(","))
    result = tap_until(a.button, a.expected, a.delay, a.tries,
                       popups=not a.no_popups, verbose=True)
    if result:
        template, (cx, cy, score) = result
        print(f"Found {Path(template).name} at ({cx}, {cy}), score {score:.3f}")
    else:
        print(f"Expected element not seen after {a.tries} taps")
        sys.exit(1)
