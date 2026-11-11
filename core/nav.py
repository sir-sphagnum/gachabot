"""Tap a UI element until an expected element shows up, closing popups on the way.

Usage: python -m core.nav BUTTON EXPECTED [EXPECTED ...] [--delay S] [--tries N]
                          [--no-popups]

Games sometimes swallow a tap (e.g. a popup that ignores input while it is
still animating in). tap_until taps BUTTON, then keeps checking the screen for
EXPECTED for `delay` seconds; if it hasn't appeared, it taps again, up to
`tries` taps. It stops as soon as any EXPECTED element is on screen with no
known popup open, including before the first tap.

The known popups are the game's common popups (<game>/templates/common/popups/,
see core/tree.py). Whenever one is open, it taps that popup's close button until
the popup is gone, then looks again. Closing a popup doesn't use up one of the
`tries`; up to `tries` popups are closed.

BUTTON is a template file or an X,Y point (e.g. 1869,49); EXPECTED are
template files. Template names that follow the map skill's scheme
(btn_/info_..._X-Y-W-H[_white].png) are searched only in their box, matching
white-only when the name says so; any other file is searched over the whole
screen. Exits 0 when an expected element was seen, 1 otherwise.

route and goto walk a game's menu tree (core.tree.load) with tap_until: each
game wires goto up in its own <game>/nav.py (e.g. e7/nav.py).
"""

import argparse
import sys
from collections import deque
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
    popups: which popups to close before trusting a match or tapping. True: the popups of the
        game the templates live in (<game>/templates/...). A game name: that
        game's popups. A dict from core.tree.load_popups. False/None: none.
    Returns (template, (cx, cy, score)) for the expected element that was
    found with no known popup open, or None if it never appeared, a popup
    couldn't be closed, or more than `tries` popups were closed.
    """
    if isinstance(button, (list, tuple)):
        button = tuple(int(v) for v in button)  # accept [x, y] as well as (x, y)
    if isinstance(expected, (str, Path)):
        expected = [expected]
    say = print if verbose else (lambda *a: None)
    known = _resolve_popups(popups, [button, *expected])

    taps = closed = 0
    while True:
        screen = capture()
        # Popups before `expected`: a popup that dims the screen can leave
        # `expected` matching underneath it.
        popup = open_popup(known, screen)
        if popup:
            if closed == tries:
                say(f"Popups still showing after closing {tries}")
                return None
            closed += 1
            say(f"Popup {popup} is open; closing it")
            if not close_popup(known[popup], delay, tries, say):
                say(f"Couldn't close popup {popup}")
                return None
            continue

        hit = _first(expected, screen)
        if hit:
            return hit
        if taps == tries:
            return None

        taps += 1
        _tap(button, screen, f"Tap {taps}/{tries}", say)
        _wait_for(lambda s: open_popup(known, s) or _first(expected, s), delay)


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


def dialog(info, close):
    """A dialog that isn't one of the game's common popups (e.g. one a menu
    opens on a known action), in the form open_popup, close_popup and
    tap_until's `popups` take. info: template path, or a list of them, that
    all match while it is open. close: template path of the button that
    closes it."""
    info = [info] if isinstance(info, (str, Path)) else info
    return {"info": [{"file": i} for i in info], "close": {"file": close}}


def _is_open(popup, screen):
    return bool(popup["info"]) and all(locate(i["file"], screen) for i in popup["info"])


def _resolve_popups(popups, templates):
    if not popups:
        return {}
    if isinstance(popups, dict):
        return popups
    if isinstance(popups, str):
        return game_popups(popups)
    for t in templates:  # popups=True: infer the game from the template paths
        if isinstance(t, tuple):
            continue
        try:
            parts = Path(t).resolve().relative_to(ROOT).parts
        except ValueError:
            continue
        if len(parts) > 1 and parts[1] == "templates":
            return game_popups(parts[0])
    return {}


@cache
def game_popups(game):
    """The popups of `game` (from core.tree.load_popups) that the bot can both
    detect (info_ images) and close (a close button), keyed by name."""
    return {n: p for n, p in load_popups(game)[0].items() if p["info"] and p["close"]}


def _first(templates, screen):
    for t in templates:
        match = locate(t, screen)
        if match:
            return str(t), match
    return None


def route(menus, start, target):
    """Shortest chain of buttons from menu `start` to menu `target`.

    menus: a game's menus from core.tree.load. Every btn_ image is an edge
    from the menu it sits on to the menu it opens, links included.
    Returns a list of (menu, button) pairs, button being a core.tree element
    entry; [] when start is target; None when no buttons lead there.
    """
    before = {start: None}
    todo = deque([start])
    while todo:
        name = todo.popleft()
        if name == target:
            steps = []
            while before[name]:
                name, button = before[name]
                steps.append((name, button))
            return steps[::-1]
        for b in menus[name]["buttons"]:
            if b["name"] in menus and b["name"] not in before:
                before[b["name"]] = (name, b)
                todo.append(b["name"])
    return None


def identity(menu):
    """Templates that show `menu` (a core.tree entry) is on screen, any one
    being enough: its info_ images, or its btn_ images if it has none."""
    return [e["file"] for e in menu["info"] or menu["buttons"]]


def goto(menus, target, home, start, here=None, ready=None, attempts=2,
         delay=1.5, tries=5, verbose=False):
    """Take the game to menu `target` by tapping down the tree from `start`.

    home: callable that brings the game to menu `start` from anywhere, in a
        state where its buttons show; returns True on success.
    start: name of the menu `home` reaches.
    here: name of the menu already on screen, to walk from there without
        calling `home` first. Only for the first attempt.
    ready: {menu: callable} for menus whose buttons show only in one state
        (e.g. a lobby that hides its HUD when idle). It is called right before
        tapping a button on that menu and returns True once they show.
    attempts: walks to try. A walk that fails (a popup that sends the game
        elsewhere, a button that isn't on screen) starts over from `home`.
    Each step is a tap_until on the button, expecting identity(next menu),
    with the game's popups closed on the way.
    Returns True once `target` is on screen, False otherwise.
    """
    say = print if verbose else (lambda *a: None)
    if target not in menus:
        raise ValueError(f"No menu '{target}'")
    ready = ready or {}
    for attempt in range(1, attempts + 1):
        origin = here if attempt == 1 and here else start
        steps = route(menus, origin, target)
        if steps is None:
            say(f"No buttons lead from {origin} to {target}")
            if origin == start:
                return False
            continue
        if origin == start:
            say(f"Going to {start}")
            if not home():
                say(f"Couldn't reach {start}")
                continue
        say("Route: " + " > ".join([origin, *(b["name"] for _, b in steps)]))
        if _walk(menus, steps, ready, delay, tries, say):
            say(f"On {target}")
            return True
    return False


def _walk(menus, steps, ready, delay, tries, say):
    for menu, button in steps:
        if menu in ready and not ready[menu]():
            say(f"{menu} isn't ready for its buttons")
            return False
        nxt = button["name"]
        say(f"{menu} > {nxt}")
        if not tap_until(button["file"], identity(menus[nxt]), delay, tries, verbose=False):
            say(f"{nxt} didn't show after tapping {button['file'].name}")
            return False
    return True


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
