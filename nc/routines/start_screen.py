"""Get past the Neural Cloud start screen (title art, GAME START) into the lobby.

Usage: python -m nc.routines.start_screen [--debug]

1. Wait for the start screen, the lobby, or a popup or lobby dialog to show
   (the game may still be loading, e.g. right after `python -m nc.bot start`).
   Already in the lobby: done.
2. Tap GAME START, waiting for it to fade in first if the start screen shows
   without it. Tap again if it is still up after a moment.
3. Wait for the lobby (its Explore title) while the game loads. If GAME
   START shows again meanwhile, the tap was ignored: tap again (step 2).

GAME START counts as gone only once it has stayed missing for GONE seconds
(.claude/doc_policy.md Rule 2): one capture without it proves nothing.

The lobby counts only when no popup or lobby dialog is open: the popups after
GAME START (notice, then login-reward over monthly-signin on the first
launch of the day) sit over the lobby. One is left open and the routine
returns True, its part done; the lobby routine, which hands over to this one
and runs after it, closes them and looks again.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import held, locate, open_popup
from nc.config import TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
GAME_START = START / "btn_start-screen_lobby_675-865-570-58.png"
# "(c) Sunborn Inc. All rights reserved.": marks the start screen. Not the
# PROJECT.NEURAL.CLOUD line, which the launch loading screen shows too.
COPYRIGHT = START / "info_start-screen_copyright_790-1036-336-34.png"
EXPLORE = START / "lobby" / "info_lobby_explore-title_1316-290-212-64.png"
GONE = 1.5  # seconds GAME START must stay missing to count as gone


def run(appear=60, taps=3, delay=5, load=60, fade=20):
    """Return True once past the start screen, with the lobby showing or a popup
    open for the lobby routine to close; False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
        From launch it took ~12 s (a loading screen, then the start screen).
    taps: maximum taps on GAME START.
    delay: seconds to wait for GAME START to go after each tap. It stayed
        ~2.1 s after a tap that took, longer on a slower start.
    load: seconds to wait for the lobby once GAME START has gone. The load
        to the first popup took ~10 s.
    fade: seconds to wait for GAME START once the start screen shows without
        it: the copyright line shows before GAME START has faded in.
    """
    found = wait_until(_look, appear)
    if found is None:
        log.error(f"no start screen or lobby after {appear}s")
        return False
    state, screen = found
    if state != "start":
        return _report(state)

    tapped = 0
    while True:
        if not locate(GAME_START, screen):
            log.debug("start screen without GAME START, waiting")
            screen = wait_until(_with_start, fade)
            if screen is None:
                log.error(f"no GAME START {fade}s after the start screen showed")
                return False
        if tapped == taps:
            log.error(f"GAME START still showing after {taps} taps")
            return False
        tapped += 1
        x, y = tap(*locate(GAME_START, screen)[:2])
        log.debug(f"tap {tapped}/{taps} at ({x}, {y})")
        if _gone(delay + GONE) is None:
            screen = _with_start()
            if screen is not None:
                continue
        log.info("left start screen, waiting for lobby")
        found = wait_until(_after_tap, load)
        if found is None:
            log.error(f"no lobby {load}s after start screen")
            return False
        state, screen = found
        if state != "start":
            return _report(state)
        log.warning("GAME START showing again, tap ignored")


def at_start_screen(screen=None):
    """True when the start screen is on screen (its copyright line shows)."""
    screen = capture() if screen is None else screen
    return bool(locate(COPYRIGHT, screen))


def _state(screen):
    """"popup", "start", "lobby", or None for anything else."""
    from nc.routines import lobby  # lobby imports this module
    if open_popup(lobby.popups(), screen):
        return "popup"
    if at_start_screen(screen):
        return "start"
    if locate(EXPLORE, screen):
        return "lobby"
    return None


def _look(states=("popup", "start", "lobby")):
    """(state, screen) for a fresh capture if its state is one of `states`, else None."""
    screen = capture()
    state = _state(screen)
    return (state, screen) if state in states else None


def _report(state):
    if state == "popup":
        log.info("popup open, returning to caller")
        return True
    log.info("in lobby")
    return True


def _gone(timeout):
    """A fresh capture once GAME START has been missing for GONE seconds in a
    row, or None if that doesn't happen within `timeout` seconds."""
    return held(lambda screen: None if locate(GAME_START, screen) else screen, GONE, timeout)


def _with_start():
    """A fresh capture if GAME START is on it, else None."""
    screen = capture()
    return screen if locate(GAME_START, screen) else None


def _after_tap():
    """(state, screen) once the lobby, a popup or GAME START shows, else None."""
    found = _look(("popup", "lobby"))
    if found:
        return found
    screen = _with_start()
    return None if screen is None else ("start", screen)


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
