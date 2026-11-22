"""Take a game from wherever it is (just launched, its start screen, any
menu) to its lobby, from the game's spec (Lobby).

Usage: python -m core.lobby GAME classify CAPTURE [CAPTURE ...]

Each game's <game>/routines/lobby.py holds its spec as SPEC and exposes
SPEC.run as run() and SPEC.popups as popups(). core.nav loads that module by
name as the start of every menu walk, and core.device.run_to_lobby runs it
after starting the game.

classify: say which step of the loop each saved capture falls into,
without touching the game, to check a spec against the game's captures.

The loop looks at the screen and acts on the first of these that fits,
then looks again:

1. black: wait it out (core.nav.past_black).
2. a stop screen: give up untouched (core.nav.stop_screen).
3. a loading screen: wait it out (core.nav.past_loading).
4. a common popup or lobby dialog: close it (popups()). Checked before the
   lobby because a popup's dim leaves the lobby's indicator matching
   (core/notes/UI.md Rule 1), and closing one can open the next.
5. the lobby (every indicator image matches): done. Once the loop has
   acted, the lobby must first hold `settle` seconds with no popup:
   popups open a moment after the lobby is drawn (common: Lobbies).
6. the idle lobby (HUD hidden): tap its wake point until the HUD shows.
7. the start screen: tap START until it has stayed gone `start.gone`
   seconds (Rule 2). While START isn't showing (fading in, or the game
   logging in after a tap) it waits.
8. a menu of the game's tree: press Back.
9. anything else is an unknown screen. During a quiet window it waits for
   a known one: the first `launch` seconds of the game's process, `start.load`
   seconds after a START tap, or a popup's `quiet_after` seconds. Back
   pressed there would be a guess (common: Loading screens). Otherwise, or
   when the wait ends on it, the screen is saved (core.unknown) and the
   loop presses Back.
"""

import argparse
import importlib
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from core import tree
from core.device import uptime, wait_until
from core.input import back, capture, tap
from core.log import logger, setup
from core.nav import (close_popup, describe, game_popups, held, loading, locate, open_popup,
                      past_black, past_loading, stop_screen, tap_until)
from core.vision import is_black, load

log = logger(__file__)


@dataclass
class StartScreen:
    """The title screen between launch and the lobby."""
    identify: list           # info_ images that all match on it, START showing or not
    tap: Path | tuple        # START: a template, or a point for a pulsing label (common: Moving parts)
    # info_ images that all show once START can be tapped, when `tap` is a
    # point (ba's title plays a movie before its buttons show). Without them,
    # a template START is its own sign, and a point is tapped whenever the
    # start screen shows.
    ready: list = field(default_factory=list)
    load: float = 60         # seconds after a START tap that unknown screens are waited on
    fade: float = 20         # seconds to wait for START while the screen shows without it
    gone: float = 1.5        # seconds START must stay missing for the tap to count (Rule 2)
    # START taps in all: a start screen that keeps coming back (an error that
    # loops to it) is one the loop can't get past.
    taps: int = 9


@dataclass
class Idle:
    """The lobby with its HUD hidden (common: Lobbies)."""
    identify: list           # info_ images that all match on it
    wake: tuple              # a point that is safe to tap, which brings the HUD back


@dataclass
class Lobby:
    game: str
    back_key: str
    indicator: list          # info_ images that all match only on the lobby with its HUD up
    start: StartScreen
    dialogs: dict = field(default_factory=dict)  # core.nav.dialog() entries only the lobby opens
    # Popups checked after every other one: one whose identifier still
    # matches under a dialog opened over it (ak's pre-start diamond).
    last: tuple = ()
    idle: Idle | None = None
    launch: float = 45       # seconds after the process starts that unknown screens are waited on
    settle: float = 3        # seconds the lobby must hold with no popup once the loop has acted
    # {popup: seconds} to wait on unknown screens after closing it (e7's
    # patch-update, whose close starts a download nothing is mapped on).
    quiet_after: dict = field(default_factory=dict)

    def popups(self):
        """The game's common popups and the lobby's dialogs, in the form
        core.nav takes, `last` at the end: open_popup returns the first that
        matches, so a dialog over one of them is found and closed first."""
        found = {**game_popups(self.game), **self.dialogs}
        return {**{k: v for k, v in found.items() if k not in self.last},
                **{k: found[k] for k in self.last if k in found}}

    def classify(self, screen, known=None):
        """(step, detail) for `screen`, as the loop would read it: "black",
        "stop", "loading", "popup", "lobby", "idle", "start", "menu" or
        "unknown". detail names the stop, popup or menu; for "start", whether
        START shows; for "unknown", None."""
        known = self.popups() if known is None else known
        if is_black(screen):
            return "black", None
        stop = stop_screen(self.game, screen)
        if stop:
            return "stop", stop
        if loading(self.game, screen):
            return "loading", None
        popup = open_popup(known, screen)
        if popup:
            return "popup", popup
        if self._lobby(screen):
            return "lobby", None
        if self.idle and _all(self.idle.identify, screen):
            return "idle", None
        if _all(self.start.identify, screen):
            return "start", self._start_shows(screen)
        said = describe(self.game, screen)
        if said:
            return "menu", said[0]
        return "unknown", None

    def run(self, backs=10, delay=1.5):
        """Return True once the lobby is on screen with its HUD, False if it couldn't get there.

        backs: maximum Back presses (reset at each START tap), and maximum
            popups and dialogs closed, wakes and lobby holds.
        delay: seconds to keep checking the screen after each press or tap.
        """
        known = self.popups()
        screen = capture()
        presses = closed = wakes = settles = started = 0
        acted = False   # a Back, close, load, wake or START tap since the last look
        quiet = 0.0     # time.monotonic() until which unknown screens are waited on
        stalled = None  # time.monotonic() the start screen was first seen without START
        while True:
            screen = past_black(screen)
            step, detail = self.classify(screen, known)
            if step != "start":
                stalled = None

            if step == "stop":
                log.error(f"stop_{detail} showing: the user's call, not acting on it")
                return False

            if step == "loading":
                screen = past_loading(self.game, screen)
                if screen is None:
                    log.error("not reached, stuck on a loading screen")
                    return False
                acted = True
                continue

            if step == "popup":
                if closed == backs:
                    log.error(f"popups still showing after closing {backs}")
                    return False
                closed += 1
                log.warning(f"popup_{detail} open, closing")
                if not close_popup(detail, known[detail], delay):
                    log.error(f"popup_{detail} not closed")
                    return False
                if detail in self.quiet_after:
                    quiet = max(quiet, time.monotonic() + self.quiet_after[detail])
                    log.info(f"popup_{detail} closed, waiting up to {self.quiet_after[detail]}s "
                             "for a known screen")
                screen = capture()
                acted = True
                continue

            if step == "lobby":
                if acted:
                    if settles == backs:
                        log.error(f"lobby never held {self.settle}s with no popup in {backs} looks")
                        return False
                    settles += 1
                    log.debug(f"lobby showing, watching {self.settle}s for popups")
                    if held(lambda s: self._clear(s, known), self.settle,
                            self.settle + delay) is None:
                        screen = capture()  # a popup opened, or the lobby went: look again
                        continue
                log.info("reached")
                return True

            if step == "idle":
                if wakes == backs:
                    log.error(f"HUD not woken after {backs} tries")
                    return False
                wakes += 1
                log.info("lobby idle, waking HUD")
                tap_until(self.idle.wake, self._lobby_check, delay, 3, popups=known)
                screen = capture()
                acted = True
                continue

            if step == "start":
                if not detail:  # START fading in, or the game logging in after a tap
                    stalled = stalled or time.monotonic()
                    left = stalled + self.start.fade + self.start.load - time.monotonic()
                    if left <= 0:
                        log.error(f"start screen without START for "
                                  f"{self.start.fade + self.start.load:g}s")
                        return False
                    log.debug("start screen without START, waiting")
                    found = wait_until(lambda: self._moved_on(capture(), known), left)
                    screen = capture() if found is None else found
                    continue
                if started == self.start.taps:
                    log.error(f"start screen still showing after {self.start.taps} START taps")
                    return False
                started += 1
                log.info(f"start screen, tapping START ({started}/{self.start.taps})")
                self._tap_start(screen)
                gone = held(lambda s: None if self._start_shows(s) else s, self.start.gone,
                            delay + self.start.gone)
                if gone is not None:
                    log.info("left start screen, waiting for the lobby")
                    quiet = max(quiet, time.monotonic() + self.start.load)
                presses = 0
                acted = True
                screen = capture()
                continue

            # A menu of the tree, or an unknown screen.
            if step == "unknown":
                left = self._quiet_left(quiet)
                if left > 0:
                    log.debug(f"unknown screen, waiting up to {left:.0f}s for a known one")
                    # The window is kept when a known screen shows: ba's first
                    # launch of the day goes load, login board, fade, cutscene,
                    # white flash, lobby, all within one START window. A wait
                    # that runs out has used the window up by the time it ends.
                    found = wait_until(lambda: self._known(capture(), known), left)
                    acted = True
                    if found is not None:
                        screen = found
                        continue
                    screen = capture()
                    if self.classify(screen, known)[0] != "unknown":
                        continue
                    waited = f"waited {left:.0f}s, "
                else:
                    waited = ""
                _save_unknown(self.game, screen, waited + (
                    "giving up" if presses == backs else f"pressing back {presses + 1}/{backs}"))
            if presses == backs:
                log.error(f"not reached after {backs} backs")
                return False
            presses += 1
            log.debug(f"back {presses}/{backs}" + (f" on {detail}" if step == "menu" else ""))
            back(self.back_key)
            acted = True
            screen = wait_until(lambda: self._lobby_capture(), delay)
            if screen is None:
                screen = capture()

    # --- checks ---------------------------------------------------------

    def _lobby(self, screen):
        return _all(self.indicator, screen)

    def _lobby_check(self, screen):
        return screen if self._lobby(screen) else None

    def _lobby_capture(self):
        screen = capture()
        return screen if self._lobby(screen) else None

    def _clear(self, screen, known):
        """`screen` if the lobby shows on it with no popup or dialog open, else None."""
        return screen if self._lobby(screen) and not open_popup(known, screen) else None

    def _start_shows(self, screen):
        """True when START can be tapped: its `ready` images show, else its
        template matches, else, for a point, the start screen itself shows."""
        if self.start.ready:
            return _all(self.start.ready, screen)
        if isinstance(self.start.tap, tuple):
            return _all(self.start.identify, screen)
        return bool(locate(self.start.tap, screen))

    def _tap_start(self, screen):
        if isinstance(self.start.tap, tuple):
            x, y = tap(*self.start.tap)
        else:
            x, y = tap(*locate(self.start.tap, screen)[:2])
        log.debug(f"START at ({x}, {y})")

    def _known(self, screen, known):
        """`screen` if the loop knows what to do on it, else None."""
        return None if self.classify(screen, known)[0] == "unknown" else screen

    def _moved_on(self, screen, known):
        """`screen` once START shows on it or the start screen has gone, else None."""
        step, shows = self.classify(screen, known)
        return screen if step != "start" or shows else None

    def _quiet_left(self, quiet):
        """Seconds left in the current quiet window: the launch wait or one opened by the loop."""
        left = quiet - time.monotonic()
        age = uptime(self.game)
        if age is not None:
            left = max(left, self.launch - age)
        return left


def _all(templates, screen):
    return bool(templates) and all(locate(t, screen) for t in templates)


def _save_unknown(game, screen, doing):
    from core import unknown  # core.unknown imports core.nav, which this module imports too
    unknown.save(game, screen, doing)


def spec(game):
    """The game's Lobby spec: SPEC in <game>/routines/lobby.py, loaded by name
    (core never imports a game package directly)."""
    return importlib.import_module(f"{game}.routines.lobby").SPEC


def _main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("game", help="the game's folder name (e.g. e7)")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("classify", help="say which step of the loop each capture falls into")
    c.add_argument("captures", nargs="+")
    a = p.parse_args()
    setup(console=False)
    if a.game not in tree.games():
        sys.exit(f"No game '{a.game}'. Games: {', '.join(tree.games())}")
    lobby = spec(a.game)
    known = lobby.popups()
    for path in a.captures:
        step, detail = lobby.classify(load(path), known)
        if step == "start":
            detail = "START showing" if detail else "no START"
        print(f"{path}: {step}" + (f" {detail}" if detail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
