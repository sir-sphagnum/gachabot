"""Tap until an element shows (closing popups) and walk a game's menu tree.

Usage: python -m core.nav GAME goto MENU [--here MENU] [--debug]
       python -m core.nav GAME routes
       python -m core.nav GAME tap BUTTON EXPECTED [EXPECTED ...] [--delay S]
                                   [--tries N] [--no-popups] [--debug]

GAME is a game's folder name (e.g. e7). --debug also logs each tap and wait.

tap: Games sometimes swallow a tap (e.g. a popup that ignores input while it is
still animating in). tap_until taps BUTTON, then keeps checking the screen for
EXPECTED for `delay` seconds; if it hasn't appeared, it taps again, up to
`tries` taps. It stops as soon as any EXPECTED element is on screen with no
known popup open, including before the first tap.

The known popups are GAME's common popups (<game>/templates/common/popups/,
see core/tree.py). Whenever one is open, it taps that popup's close button until
the popup is gone, then looks again. Closing a popup doesn't use up one of the
`tries`; up to `tries` popups are closed.

BUTTON is a template file or an X,Y point (e.g. 1869,49); EXPECTED are
template files. Template names that follow the map skill's scheme
(btn_/info_..._X-Y-W-H[_white].png) are searched only in their box, matching
white-only when the name says so; any other file is searched over the whole
screen. Exits 0 when an expected element was seen, 1 otherwise.

goto: take GAME to MENU, a menu folder name under <game>/templates/,
from wherever it is. Every walk starts from the game's lobby: its menu folder
named `lobby`, reached by the game's lobby routine. Then it taps down the
tree's btn_ images with tap_until. --here names the menu already on screen,
to walk from it instead. Exits 0 once MENU is on screen, 1 otherwise.

routes: print each menu's route from the lobby, without touching the game.

goto and tap stop with an error, before tapping anything, unless GAME is the
app in focus and fullscreen (not floating).
"""

import argparse
import importlib
import sys
from collections import deque
from functools import cache
from pathlib import Path

from core import ROOT, tree
from core.device import floating_window, focused_app, is_running, package, wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.tree import ELEMENT, load_popups
from core.vision import find, is_black

log = logger(__file__)

# Every game has a menu folder by this name, and a <game>/routines/lobby.py
# whose run() brings the game there from anywhere, with its buttons showing,
# and returns True once it has.
HOME = "lobby"

BLACK_WAIT = 30  # seconds to wait out a black loading or transition screen


class NotInFocus(RuntimeError):
    """The game isn't the app in focus, fullscreen. Not in focus, taps and Back
    presses land on whatever app is; floating, the screen is scaled down and
    templates (cut from 1920x1080 captures) don't match it."""


def check_focus(game):
    """Raise NotInFocus unless `game` is the app in focus and fullscreen."""
    pkg = package(game)
    focus = focused_app()
    if not focus or focus[0] != pkg:
        state = "is running but not in focus" if is_running(game) else "is not running"
        front = focus[0] if focus else "nothing"
        raise NotInFocus(f"{game} ({pkg}) {state}; in focus: {front}. "
                         f"Start it with: python -m core.device start --fullscreen {game}")
    if floating_window():
        raise NotInFocus(f"{game} ({pkg}) is in focus but in a floating window, not "
                         f"fullscreen. Fullscreen it with: python -m core.device fullscreen")


def tap_until(button, expected, delay=1.5, tries=5, popups=True):
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
    couldn't be closed, or more than `tries` popups were closed. Each None
    logs its reason as a WARNING, so the caller logs only what it gives up on.
    While the screen is black it neither taps nor looks: it waits (past_black).
    """
    if isinstance(button, (list, tuple)):
        button = tuple(int(v) for v in button)  # accept [x, y] as well as (x, y)
    if isinstance(expected, (str, Path)):
        expected = [expected]
    known = _resolve_popups(popups, [button, *expected])

    taps = closed = 0
    while True:
        screen = past_black()
        # Popups before `expected`: a popup that dims the screen can leave
        # `expected` matching underneath it.
        popup = open_popup(known, screen)
        if popup:
            if closed == tries:
                log.warning(f"popups still showing after closing {tries}")
                return None
            closed += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, known[popup], delay, tries):
                return None
            continue

        hit = _first(expected, screen)
        if hit:
            return hit
        if taps == tries:
            log.warning(f"expected element not seen in {tries} tries")
            return None

        taps += 1
        _tap(button, screen, f"tap {taps}/{tries}")
        _wait_for(lambda s: open_popup(known, s) or _first(expected, s), delay)


def past_black(screen=None, timeout=BLACK_WAIT):
    """The current screen once it isn't black (core.vision.is_black).

    A black screen is a load or a transition: nothing on it matches yet, so
    any decision taken on it (tap again, press Back) is a guess. Callers use
    this to look only once the game has drawn something.
    screen: a capture to start from; a fresh one is taken when None.
    Waits up to `timeout` seconds, then returns the last capture, black or not.
    """
    screen = capture() if screen is None else screen
    if not is_black(screen):
        return screen
    log.debug("black screen, waiting")
    screen = wait_until(lambda: _unless_black(capture()), timeout)
    if screen is None:
        log.warning(f"still black after {timeout}s, going on")
        return capture()
    return screen


def _unless_black(screen):
    return None if is_black(screen) else screen


def open_popup(popups, screen):
    """Name of the first popup in `popups` that is open on `screen`, or None.
    A popup is open when all of its info_ images match."""
    for name, popup in popups.items():
        if _is_open(popup, screen):
            return name
    return None


def close_popup(name, popup, delay=1.5, tries=5):
    """Tap `popup`'s close button until the popup is gone. Returns True once
    it is gone, False (logged as a WARNING) if it is still open after `tries`
    taps. name: the popup's key in its popups dict, for the log."""
    for attempt in range(1, tries + 1):
        screen = capture()
        if not _is_open(popup, screen):
            return True
        _tap(popup["close"]["file"], screen, f"popup_{name}: close tap {attempt}/{tries}")
        if _wait_for(lambda s: not _is_open(popup, s), delay):
            return True
    if not _is_open(popup, capture()):
        return True
    log.warning(f"popup_{name} still open after {tries} close taps")
    return False


def _tap(button, screen, label):
    match = (*button, 1.0) if isinstance(button, tuple) else locate(button, screen)
    if match:
        cx, cy, _ = match
        tap(cx, cy)
        log.debug(f"{label} at ({cx}, {cy})")
    else:
        log.warning(f"{label} skipped: {Path(button).name} not on screen")


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


def lobby(game):
    """The game's lobby routine: <game>.routines.lobby.run.

    Loaded by name, since core never imports a game package directly."""
    return importlib.import_module(f"{game}.routines.lobby").run


def routes(game):
    """{menu: [menu names from HOME to it], or None when unreachable}."""
    menus, _ = tree.load(game)
    out = {}
    for name in menus:
        steps = route(menus, HOME, name) if HOME in menus else None
        out[name] = None if steps is None else [HOME, *(b["name"] for _, b in steps)]
    return out


def goto(game, target, here=None, attempts=2, delay=1.5, tries=5):
    """Take `game` to menu `target` by tapping down its tree from HOME.

    here: name of the menu already on screen, to walk from there without
        going to HOME first. Only for the first attempt.
    attempts: walks to try. A walk that fails (a popup that sends the game
        elsewhere, a button that isn't on screen) starts over from HOME.
    Each step is a tap_until on the button, expecting identity(next menu),
    with the game's popups closed on the way.
    Returns True once `target` is on screen, False otherwise. Raises
    NotInFocus, before touching anything, unless `game` is the app in focus
    and fullscreen.
    """
    menus, _ = tree.load(game)
    for name in (target, here, HOME):
        if name and name not in menus:
            raise ValueError(f"No menu '{name}' in {game}")
    check_focus(game)
    home = lobby(game)
    for attempt in range(1, attempts + 1):
        last = attempt == attempts
        origin = here if attempt == 1 and here else HOME
        steps = route(menus, origin, target)
        if steps is None:
            if origin == HOME:
                log.error(f"no route from {HOME} to {target}")
                return False
            log.warning(f"no route from {origin} to {target}"
                        + ("" if last else f", walking from {HOME}"))
            continue
        if origin == HOME:
            log.info(f"going to {HOME}")
            if not home():
                log.warning(f"{HOME} not reached" + ("" if last else ", restarting walk"))
                continue
        log.info("route: " + " > ".join([origin, *(b["name"] for _, b in steps)]))
        stopped = _walk(menus, steps, home, delay, tries)
        if not stopped:
            log.info(f"on {target}")
            return True
        log.warning(stopped + ("" if last else ", restarting walk"))
    log.error(f"{target} not reached after {attempts} attempts")
    return False


def _walk(menus, steps, home, delay, tries):
    """Tap down `steps`. Returns None once done, or why it stopped."""
    for menu, button in steps:
        # A lobby may hide its buttons when idle (E7's after ~9 s), so run the
        # lobby routine right before each tap on it. When they already show,
        # that costs only a few captures.
        if menu == HOME and not home():
            return f"{HOME} buttons not showing"
        nxt = button["name"]
        log.info(f"{menu} > {nxt}")
        if not tap_until(button["file"], identity(menus[nxt]), delay, tries):
            return f"{nxt} not shown after tapping {button['file'].name}"
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


def _main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("game", help="the game's folder name (e.g. e7)")
    sub = p.add_subparsers(dest="cmd", required=True)
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument("--debug", action="store_true", help="also log each tap and wait")
    g = sub.add_parser("goto", parents=[debug],
                       help="take the game to MENU, starting from its lobby")
    g.add_argument("menu")
    g.add_argument("--here", help="the menu already on screen")
    sub.add_parser("routes", help="print each menu's route from the lobby")
    t = sub.add_parser("tap", parents=[debug],
                       help="tap BUTTON until an EXPECTED element shows")
    t.add_argument("button")
    t.add_argument("expected", nargs="+")
    t.add_argument("--delay", type=float, default=1.5,
                   help="seconds to wait for EXPECTED after each tap (default 1.5)")
    t.add_argument("--tries", type=int, default=5, help="maximum taps (default 5)")
    t.add_argument("--no-popups", action="store_true", help="don't look for popups")
    a = p.parse_args()
    setup(getattr(a, "debug", False))
    if a.game not in tree.games():
        sys.exit(f"No game '{a.game}'. Games: {', '.join(tree.games())}")
    try:
        return _run(a)
    except NotInFocus as e:
        sys.exit(f"Error: {e}")


def _run(a):
    if a.cmd == "routes":
        for name, path in routes(a.game).items():
            print(f"{name}: {' > '.join(path) if path else f'(not reachable from the {HOME})'}")
        return 0

    if a.cmd == "goto":
        menus, _ = tree.load(a.game)
        for name in (a.menu, a.here):
            if name and name not in menus:
                sys.exit(f"No menu '{name}'. Menus: {', '.join(menus)}")
        return 0 if goto(a.game, a.menu, a.here) else 1

    if "," in a.button and not Path(a.button).exists():
        a.button = tuple(int(v) for v in a.button.split(","))
    check_focus(a.game)
    result = tap_until(a.button, a.expected, a.delay, a.tries,
                       popups=None if a.no_popups else a.game)
    if not result:
        print(f"Expected element not seen after {a.tries} taps")
        return 1
    template, (cx, cy, score) = result
    print(f"Found {Path(template).name} at ({cx}, {cy}), score {score:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
