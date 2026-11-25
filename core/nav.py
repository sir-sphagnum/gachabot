"""Tap until an element shows (closing popups) and walk a game's menu tree.

Usage: python -m core.nav GAME goto MENU [--here MENU] [--debug]
       python -m core.nav GAME routes
       python -m core.nav GAME where [CAPTURE]
       python -m core.nav GAME tap BUTTON EXPECTED [EXPECTED ...] [--delay S]
                                   [--tries N] [--no-popups] [--debug]
       python -m core.nav GAME wait EXPECTED [EXPECTED ...] --timeout S
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
(btn_/info_..._X-Y-W-H[_anywhere][_white].png) are searched only in their box
(over the whole screen when the name says _anywhere), matching white-only when
the name says _white; any other file is searched over the whole screen. Exits 0 when an expected element was seen, 1 otherwise.

wait: wait_clear from the command line, for a result no tap brings (a
fight's end, a long load) when Claude drives the game by hand (Rule 7): waits
up to --timeout seconds for an EXPECTED element with no known popup open,
closing popups as they open (up to --tries). Exits 0 when one showed, 1 with
an ERROR and its error screen otherwise.

goto: take GAME to MENU, a menu folder name under <game>/templates/,
from wherever it is. Every walk starts from the game's lobby: its menu folder
named `lobby`, reached by the game's lobby routine. Then it taps down the
tree's btn_ images with tap_until. --here names the menu already on screen,
to walk from it instead. Exits 0 once MENU is on screen, 1 otherwise.

routes: print each menu's route from the lobby, without touching the game.

where: name the stop screen or loading screen showing, the common popups
open and every menu whose identifying images match, best score first, on the
screen or on a saved CAPTURE. More than one menu can match (shared
identifiers, a menu under a popup's dim). Exits 1 when nothing matches.

goto and tap stop with an error, before tapping anything, unless GAME is the
app in focus and fullscreen (not floating).
"""

import argparse
import importlib
import sys
import time
from collections import deque
from functools import cache
from pathlib import Path

import cv2

from core import ROOT, steps, templates_dir, tree
from core.device import floating_window, focused_app, is_running, package, wait_until
from core.input import capture, swipe, tap
from core.log import logger, setup
from core.tree import ELEMENT, load_popups, load_stops
from core.vision import difference, find, fingerprint, is_black, load

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
                         f"Start it with: python -m core.device start {game}")
    if floating_window():
        raise NotInFocus(f"{game} ({pkg}) is in focus but in a floating window, not "
                         f"fullscreen. Fullscreen it with: python -m core.device fullscreen")


def tap_until(button, expected, delay=1.5, tries=5, popups=True, first=True):
    """Tap `button` until one of `expected` is on screen.

    This is how a routine taps (core/notes/UI.md Rule 2): it judges the
    tap by the screen over `delay` seconds, not by one look right after it,
    and taps again only once that time has passed with no result.

    button: template path of the element to tap, or an (x, y) point. A
        template is located on the live screen before each tap, so the tap
        lands on the match, not the stored box; if it isn't on screen, that
        round taps nothing and just waits. A point is tapped as is (e.g. an
        empty spot of a lobby, to wake its HUD).
    expected: template path, a check(screen) that returns something truthy
        once the tap took (e.g. a button reads lit by colour), or a list of
        them; stop when any one is found.
    delay: seconds to keep checking for `expected` after each tap before
        tapping again.
    tries: maximum number of taps on `button`.
    popups: which popups to close before trusting a match or tapping. True: the popups of the
        game the templates live in (<game>/templates/...). A game name: that
        game's popups. A dict from core.tree.load_popups. False/None: none.
    first: look for `expected` before the first tap. False taps at least
        once, for an `expected` that can already show before the tap (a
        Challenge button still lit from the row chosen before).
    Returns (template, (cx, cy, score)) for the expected element that was
    found with no known popup open ((check, its result) for a check), or
    None if it never appeared, a popup
    couldn't be closed, or more than `tries` popups were closed. Each None
    logs its reason as a WARNING, so the caller logs only what it gives up on.
    While the screen is black it neither taps nor looks: it waits (past_black).
    Each call adds a line to the step statistics (core.steps).
    """
    if isinstance(button, (list, tuple)):
        button = tuple(int(v) for v in button)  # accept [x, y] as well as (x, y)
    if isinstance(expected, (str, Path)) or callable(expected):
        expected = [expected]
    known = _resolve_popups(popups, [button, *expected])

    stats = {"taps": 0, "skipped": 0, "popups": 0}
    start = time.monotonic()
    hit = None
    try:
        hit = _tap_until(button, expected, delay, tries, known, first, stats)
        if hit is None:
            _gave_up(_game_of(popups, known, [button, *expected]))
        return hit
    finally:
        steps.record("tap_until", steps.name(button), game=steps.game(button, *expected),
                     expected=[steps.name(e) for e in expected],
                     found=steps.name(hit[0]) if hit else None, **stats,
                     s=round(time.monotonic() - start, 1), ok=bool(hit))


def _tap_until(button, expected, delay, tries, known, first, stats):
    while True:
        screen = past_black()
        # Popups before `expected`: a popup that dims the screen can leave
        # `expected` matching underneath it.
        popup = open_popup(known, screen)
        if popup:
            if stats["popups"] == tries:
                log.warning(f"popups still showing after closing {tries}")
                return None
            stats["popups"] += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, known[popup], delay, tries):
                return None
            continue

        hit = _first(expected, screen) if stats["taps"] or first else None
        if hit:
            return hit
        if stats["taps"] == tries:
            log.warning(f"expected element not seen in {tries} tries")
            return None

        stats["taps"] += 1
        if not _tap(button, screen, f"tap {stats['taps']}/{tries}"):
            stats["skipped"] += 1
        _wait_for(lambda s: open_popup(known, s) or _first(expected, s), delay)


def wait_clear(expected, timeout, popups=True, tries=5, delay=1.5, interval=0.5):
    """Wait up to `timeout` seconds for one of `expected` to show with no
    popup open, closing each popup that opens meanwhile.

    For a long wait on a result no tap brings (a fight's result screen, the
    end of a load): a popup that opens during it (a level-up after a fight)
    can hide the result, and a wait that only looks for the result sits
    behind it until its timeout (core/notes/UI.md, Rule 7).
    expected, popups: as tap_until takes them. tries: maximum popups closed.
    delay: seconds each close tap is given to work.
    Returns what tap_until returns, or None (logged as a WARNING) when
    nothing showed in time, a popup couldn't be closed, or more than `tries`
    were. Black screens are waited through. Each call adds a line to the
    step statistics (core.steps).
    """
    if isinstance(expected, (str, Path)) or callable(expected):
        expected = [expected]
    known = _resolve_popups(popups, expected)
    start = time.monotonic()
    stats = {"popups": 0}
    hit = None
    try:
        hit = _wait_clear(expected, timeout, known, tries, delay, interval, stats)
        if hit is None:
            _gave_up(_game_of(popups, known, expected))
        return hit
    finally:
        steps.record("wait_clear", steps.name(expected[0]), game=steps.game(*expected),
                     expected=[steps.name(e) for e in expected],
                     found=steps.name(hit[0]) if hit else None, **stats,
                     s=round(time.monotonic() - start, 1), ok=bool(hit))


def _wait_clear(expected, timeout, known, tries, delay, interval, stats):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        screen = capture()
        if is_black(screen):
            time.sleep(interval)
            continue
        popup = open_popup(known, screen)
        if popup:
            if stats["popups"] == tries:
                log.warning(f"popups still showing after closing {tries}")
                return None
            stats["popups"] += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, known[popup], delay, tries):
                return None
            continue
        hit = _first(expected, screen)
        if hit:
            return hit
        time.sleep(interval)
    log.warning(f"expected element not seen in {timeout}s")
    return None


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


LOAD_WAIT = 60  # seconds; the longest load seen took ~23 s (ba, after TOUCH TO START)


@cache
def game_loads(game):
    """The info_ images of `game`'s loading screens (<game>/templates/common/loading/),
    any one being enough. Empty for a game whose loads are all black (e7)."""
    base = templates_dir(game) / tree.COMMON / "loading"
    return tuple(sorted(base.rglob("info_*.png"))) if base.is_dir() else ()


def loading(game, screen):
    """True when one of `game`'s loading screens shows on `screen`."""
    return any(locate(t, screen) for t in game_loads(game))


def past_loading(game, screen=None, timeout=LOAD_WAIT):
    """The current screen once it is neither black nor one of `game`'s
    loading screens, or None (logged as a WARNING) if a loading screen still
    shows after `timeout` seconds.

    Nothing on a load answers Back, and a Back that lands as it ends acts on
    the screen after (core/notes/UI.md, "Loading screens"), so a routine that
    presses Back looks only at what this returns.
    screen: a capture to start from; a fresh one is taken when None.
    """
    screen = past_black(screen)
    if not loading(game, screen):
        return screen
    log.debug("loading screen, waiting")
    screen = wait_until(lambda: _unless_loading(game, past_black()), timeout)
    if screen is None:
        log.warning(f"still loading after {timeout}s")
    return screen


def _unless_loading(game, screen):
    return None if loading(game, screen) else screen


def _truthy(result):
    # A capture (numpy array) counts as truthy: its own truth value raises.
    return result is not None if hasattr(result, "shape") else bool(result)


def held(check, hold, timeout, interval=0.2):
    """check(screen)'s result once it has been truthy on every capture for
    `hold` seconds in a row, or None if that doesn't happen within `timeout`.

    For a result that can flicker (Rule 2): a button can drop out of one
    capture during its animation, or flash back for a moment after a tap
    that took, so one capture without it is no proof it's gone.
    Each call adds a line to the step statistics (core.steps), counting
    `flickers`: the times the result showed and dropped again.
    """
    start = time.monotonic()
    deadline = start + timeout
    since = None
    flickers = 0
    result = None
    try:
        while time.monotonic() < deadline:
            result = check(capture())
            if _truthy(result):
                since = since or time.monotonic()
                if time.monotonic() - since >= hold:
                    return result
            else:
                flickers += since is not None
                since = None
            time.sleep(interval)
        result = None
        return None
    finally:
        steps.record("held", steps.name(check), game=steps.game(), flickers=flickers,
                     s=round(time.monotonic() - start, 1), ok=_truthy(result))


STILL = 1.0  # percent of changed pixels (core.vision.difference) below which the screen is still


def settled(timeout, still=STILL, interval=0.3):
    """True once two captures `interval` apart barely differ (a list that
    scrolls on entry has stopped), False if it still moves after `timeout`
    seconds. Entries of a list that moves are tapped only once it's still
    (core/notes/UI.md, "Lists that move")."""
    last = [_print(past_black())]

    def _still():
        now = _print(capture())
        moved = difference(last[0], now)
        last[0] = now
        return moved < still

    return wait_until(_still, timeout, interval=interval) is not None


SCROLL_SETTLE = 3  # seconds for a list or map to stop gliding after a swipe


def scroll_to(template, points, tries=6, ms=500, timeout=SCROLL_SETTLE):
    """Bring `template` (an entry of a list, a stage on a map) on screen by
    swiping. Waits for the screen to stop moving and looks for it; while it
    isn't there, swipes `points` (x1, y1, x2, y2) over `ms` milliseconds and
    does the same, up to `tries` swipes. Returns (cx, cy, score) as `locate`
    does, read off a still screen, or None.

    A list keeps gliding after a swipe, so a capture taken during it shows the
    entry where it won't stay (core/notes/UI.md, "Lists that move"). A screen
    whose art never stops is looked at once `timeout` has passed anyway.
    """
    name = Path(template).name
    for n in range(tries + 1):
        if not settled(timeout):
            log.debug(f"still moving after {timeout}s, looking anyway")
        hit = locate(template, capture())
        if hit:
            log.debug(f"{name} on screen after {n} swipes")
            return hit
        if n < tries:
            log.debug(f"{name} not on screen, swipe {n + 1}/{tries}")
            swipe(*points, ms)
    log.warning(f"{name} not on screen after {tries} swipes")
    return None


def _print(screen):
    return fingerprint(cv2.cvtColor(load(screen), cv2.COLOR_BGR2GRAY))


def clear(popups, title=None, delay=1.5, tries=5):
    """The current screen once none of `popups` is open, and, given `title`
    (a template), once it shows; None if that can't be
    had. Like every helper here it logs why at WARNING, and the routine logs
    its ERROR (.claude/logging.md §3).

    Rule 1: a dialog's dim can leave a menu's title matching, so every check
    on a menu reads a screen from here. popups: as open_popup takes them,
    usually the game's popups plus the menu's own dialogs (`dialog`).
    Closing a popup can open another (a claim's reward); up to `tries` are
    closed.
    """
    screen = _clear(popups, title, delay, tries)
    if screen is None:
        _gave_up(_game_of(None, popups, [title] if title else []))
    return screen


def _clear(popups, title, delay, tries):
    for _ in range(tries + 1):
        screen = past_black()
        name = open_popup(popups, screen)
        if not name:
            if title is None or locate(title, screen):
                return screen
            m = ELEMENT.match(Path(title).name)
            log.warning(f"{m['menu'] if m else Path(title).name} not on screen")
            return None
        log.warning(f"popup_{name} open, closing")
        if not close_popup(name, popups[name], delay, tries):
            log.warning(f"popup_{name} not closed")
            return None
    log.warning(f"popups still showing after closing {tries}")
    return None


def open_popup(popups, screen):
    """Name of the first popup in `popups` that is open on `screen`, or None.
    A popup is open when all of its info_ images match."""
    for name, popup in popups.items():
        if _is_open(popup, screen):
            return name
    return None


# Seconds a popup must stay missing to count as closed (Rule 2). ak's pre-start
# diamond pulses around the match threshold under a launch dialog's dim, so
# it dropped out of single captures every ~0.5 s: taken as closed on one
# look, it was "closed" 10 times with 3 taps while the dialog over it, which
# the bot didn't know, blocked every tap.
CLOSED_HOLD = 1.0


def close_popup(name, popup, delay=1.5, tries=5):
    """Tap `popup`'s close button until the popup is gone. Returns True once
    it has stayed gone CLOSED_HOLD seconds, before or after a tap, False
    (logged as a WARNING) if it is still open after `tries` taps.
    name: the popup's key in its popups dict, for the log.
    Each call adds a line to the step statistics (core.steps)."""
    stats = {"taps": 0, "skipped": 0}
    start = time.monotonic()
    ok = False
    try:
        ok = _close_popup(name, popup, delay, tries, stats)
        return ok
    finally:
        steps.record("close_popup", f"popup_{name}", game=steps.game(popup["close"]["file"]),
                     **stats, s=round(time.monotonic() - start, 1), ok=ok)


def _close_popup(name, popup, delay, tries, stats):
    def gone(screen):
        return not _is_open(popup, screen)

    def stays_gone():
        return held(gone, CLOSED_HOLD, CLOSED_HOLD + delay) is not None

    for attempt in range(1, tries + 1):
        screen = capture()
        if gone(screen):
            if stays_gone():
                return True
            screen = capture()
        stats["taps"] += 1
        if not _tap(popup["close"]["file"], screen, f"popup_{name}: close tap {attempt}/{tries}"):
            stats["skipped"] += 1
        if stays_gone():
            return True
    log.warning(f"popup_{name} still open after {tries} close taps")
    return False


def _tap(button, screen, label):
    """Tap `button` where it is on `screen`. False when it isn't there (skipped)."""
    match = (*button, 1.0) if isinstance(button, tuple) else locate(button, screen)
    if match:
        x, y = tap(*match[:2])
        log.debug(f"{label} at ({x}, {y})")
        return True
    log.warning(f"{label} skipped: {Path(button).name} not on screen")
    return False


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
        if isinstance(t, tuple) or callable(t):
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


@cache
def game_stops(game):
    """The stop screens of `game` (from core.tree.load_stops) the bot can
    detect (info_ images), keyed by name."""
    return {n: s for n, s in load_stops(game)[0].items() if s["info"]}


def stop_screen(game, screen):
    """Name of the stop screen of `game` showing on `screen`, or None.

    A stop screen waits on a choice that is the user's (core/tree.py), so a
    routine that sees one taps nothing, presses no Back, and gives up with
    an ERROR naming it. Lobby routines look for one before anything else:
    on a screen they don't know they press Back."""
    return open_popup(game_stops(game), screen)


def _first(templates, screen):
    for t in templates:
        if callable(t):
            result = t(screen)
            if _truthy(result):
                return t, result
            continue
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


def identity(menus, name):
    """Templates that show menu `name` is on screen, any one being enough: its
    info_ images, or, if it has none, its buttons to other menus. Buttons that
    keep the game on the menu (claim, tab) are left out: many show only in some
    states, e.g. a claim button only while there is something to claim."""
    menu = menus[name]
    return [e["file"] for e in menu["info"]
            or [b for b in menu["buttons"] if b["name"] in menus and b["name"] != name]]


def where(game, screen):
    """What `screen` shows, as (popups, menus).

    popups: names of the game's common popups open on it.
    menus: [(menu, template file name, score)], best first, for every menu
        one of whose identity() templates matches. Several can match: some
        identifiers show on more than one menu (e.g. a scene behind a panel),
        and a popup's dim can leave the menu under it matching.
    """
    menus, _ = tree.load(game)
    popups = [n for n, p in game_popups(game).items() if _is_open(p, screen)]
    found = []
    for name in menus:
        hits = [(Path(t).name, m[2]) for t in identity(menus, name)
                for m in [locate(t, screen)] if m]
        if hits:
            found.append((name, *max(hits, key=lambda h: h[1])))
    return popups, sorted(found, key=lambda f: -f[2])


def describe(game, screen):
    """What in `game`'s templates explains `screen`, as short labels: "black",
    "stop_<name>", "loading", "popup_<name>", "<menu> (<template> <score>)".
    Empty for an unknown screen, one core.unknown saves. screen: a capture
    or a saved one's path."""
    screen = load(screen)
    if is_black(screen):
        return ["black"]
    stop = stop_screen(game, screen)
    if stop:
        return [f"stop_{stop}"]
    if loading(game, screen):
        return ["loading"]
    popups, menus = where(game, screen)
    return [f"popup_{p}" for p in popups] + [f"{m} ({t} {s:.2f})" for m, t, s in menus]


def _gave_up(game):
    """A helper gave up: save the screen it gave up on when nothing in
    `game`'s templates explains it (core.unknown). The routine's ERROR saves
    an error screen too, but only an unknown one is kept for mapping."""
    if not game:
        return
    try:
        screen = capture()
        if describe(game, screen):
            return
    except Exception as e:  # BlankScreen, AdbTimeout: the helper's own result stands
        log.warning(f"screen not checked after giving up: {e}")
        return
    from core import unknown  # core.unknown imports this module
    unknown.save(game, screen, "giving up")


def _game_of(popups, known, templates):
    """The game a helper works on: a game name passed as `popups`, else the
    game whose templates are among `templates` or the popups' close buttons,
    else the calling routine's folder (core.steps.game)."""
    if isinstance(popups, str):
        return popups
    closes = [p["close"]["file"] for p in (known or {}).values()
              if p.get("close") and isinstance(p["close"]["file"], (str, Path))]
    return steps.game(*[t for t in templates if isinstance(t, (str, Path))], *closes)


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
        # A step whose menu nothing identifies can only fail, after every tap
        # and walk: stop before touching the game.
        blind = [b["name"] for _, b in steps if not identity(menus, b["name"])]
        if blind:
            log.error(f"nothing identifies {', '.join(blind)} (no info_ image or button "
                      "to another menu), can't walk there")
            return False
        if origin == HOME:
            log.info(f"going to {HOME}")
            if not home():
                log.warning(f"{HOME} not reached" + ("" if last else ", restarting walk"))
                continue
        log.info("route: " + " > ".join([origin, *(b["name"] for _, b in steps)]))
        stopped = _walk(game, menus, origin, steps, home, delay, tries)
        if not stopped:
            log.info(f"on {target}")
            return True
        log.warning(stopped + ("" if last else ", restarting walk"))
    log.error(f"{target} not reached after {attempts} attempts")
    return False


def _walk(game, menus, origin, steps, home, delay, tries):
    """Tap down `steps` from `origin`. Returns None once done, or why it stopped."""
    passed = {origin}
    for menu, button in steps:
        # A lobby may hide its buttons when idle (E7's after ~9 s), so run the
        # lobby routine right before each tap on it. When they already show,
        # that costs only a few captures.
        if menu == HOME and not home():
            return f"{HOME} buttons not showing"
        passed.add(menu)
        nxt = button["name"]
        log.info(f"{menu} > {nxt}")
        if not tap_until(button["file"], identity(menus, nxt), delay, tries):
            _save_foreign(game, passed, f"walking {menu} > {nxt}, gave up")
            return f"{nxt} not shown after tapping {button['file'].name}"
    return None


def _save_foreign(game, passed, doing):
    """Save the screen a walk stopped on (core.unknown) when it matches menus
    the walk didn't pass through. tap_until saves only a screen nothing
    explains, but an unmapped dialog over a menu can share its title with
    other menus' dialogs (common: Shared buttons) and so count as known. A
    menu on the walk (`passed`) can still show under a panel, so only the
    others count."""
    try:
        screen = capture()
        popups, found = where(game, screen)
    except Exception as e:  # BlankScreen, AdbTimeout: the walk's own result stands
        log.warning(f"screen not checked after the walk stopped: {e}")
        return
    others = sorted({m for m, _, _ in found} - passed)
    if popups or not others:
        return
    from core import unknown  # core.unknown imports this module
    unknown.save(game, screen, f"{doing}; matches {', '.join(others)}")


def locate(template, screen, threshold=0.85):
    """Find `template` on `screen` like core.vision.find, but for map-scheme names
    (btn_/info_..._X-Y-W-H[_anywhere][_white].png) search only their box, or
    the whole screen when the name says _anywhere, white-only when it says
    _white. Returns (cx, cy, score) or None below `threshold`."""
    m = ELEMENT.match(Path(template).name)
    if not m:
        return find(template, screen, threshold=threshold)
    box = None if m["anywhere"] else tuple(int(m[k]) for k in "xywh")
    return find(template, screen, box, threshold, white=bool(m["white"]))


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
    w = sub.add_parser("where", help="name the menus and popups on screen")
    w.add_argument("capture", nargs="?", help="a saved capture to look at instead of the screen")
    t = sub.add_parser("tap", parents=[debug],
                       help="tap BUTTON until an EXPECTED element shows")
    t.add_argument("button")
    t.add_argument("expected", nargs="+")
    t.add_argument("--delay", type=float, default=1.5,
                   help="seconds to wait for EXPECTED after each tap (default 1.5)")
    t.add_argument("--tries", type=int, default=5, help="maximum taps (default 5)")
    t.add_argument("--no-popups", action="store_true", help="don't look for popups")
    wt = sub.add_parser("wait", parents=[debug],
                        help="wait for an EXPECTED element, closing popups as they open")
    wt.add_argument("expected", nargs="+")
    wt.add_argument("--timeout", type=float, required=True, help="seconds to wait at most")
    wt.add_argument("--tries", type=int, default=5, help="maximum popups closed (default 5)")
    wt.add_argument("--no-popups", action="store_true", help="don't look for popups")
    a = p.parse_args()
    setup(getattr(a, "debug", False),
          run=f"{__spec__.name}-{a.game}-{a.cmd}" if a.cmd in ("goto", "tap", "wait") else None)
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

    if a.cmd == "where":
        screen = a.capture or capture()
        stop = stop_screen(a.game, screen)
        load = loading(a.game, screen)
        popups, menus = where(a.game, screen)
        if stop:
            print(f"stop_{stop} showing")
        if load:
            print("loading screen")
        for name in popups:
            print(f"popup_{name} open")
        for name, template, score in menus:
            print(f"{name}  ({template} {score:.2f})")
        found = stop or load or popups or menus
        if not found:
            print("No known menu, popup, load or stop screen")
        return 0 if found else 1

    if a.cmd == "goto":
        menus, _ = tree.load(a.game)
        for name in (a.menu, a.here):
            if name and name not in menus:
                sys.exit(f"No menu '{name}'. Menus: {', '.join(menus)}")
        return 0 if goto(a.game, a.menu, a.here) else 1

    if a.cmd == "wait":
        check_focus(a.game)
        result = wait_clear(a.expected, a.timeout, popups=None if a.no_popups else a.game,
                            tries=a.tries)
        if not result:
            names = ", ".join(Path(e).name for e in a.expected)
            log.error(f"wait: {names} not on screen with no popup open in {a.timeout:g}s")
            return 1
        template, (cx, cy, score) = result
        print(f"Found {Path(template).name} at ({cx}, {cy}), score {score:.3f}")
        return 0

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
