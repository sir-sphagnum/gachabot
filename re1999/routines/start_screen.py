"""Get past the Reverse: 1999 start screen (title screen, START) into the lobby.

Usage: python -m re1999.routines.start_screen [--debug]

1. Wait for the start screen, the lobby, or a popup or lobby dialog to show
   (the game may still be loading, e.g. right after
   `python -m re1999.bot start`). Already in the lobby: done.
2. Tap START, waiting for it to fade in first if the start screen shows
   without it. Tap again if START is still up after a moment. START goes
   at the tap, but the logo stays ~20 s while the game logs in, so a logo
   whose START never fades in is a game already starting.
3. Wait for the lobby (its Crew button) while the game loads. If START
   shows again meanwhile, the tap was ignored: tap again (step 2).

START counts as gone only once it has been missing for GONE seconds: during
its intro animation it drops out of a capture now and then, and the game
ignores taps until the intro ends.

The lobby counts only when no popup or lobby dialog is open: Crew matches
through the quit dialog's dim. On the first launch of the day the game shows
the obtained popup, then the check-in card and event-login, before the lobby.
Any of them is left open and the routine returns True, its part done; the
lobby routine, which hands over to this one and runs after it, closes them
and looks again.
"""

import sys
import time

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import locate, open_popup
from re1999.config import TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
# Alpha-masked to its letters: an orbit spins across them.
START_BUTTON = START / "btn_start-screen_lobby_883-789-140-28.png"
# The "REVERSE 1999" logo, masked to its letters. It marks the start screen,
# not START: after the launch load the screen shows for a while without
# START, which fades in later.
LOGO = START / "info_start-screen_logo_462-350-1000-182.png"
CREW = START / "lobby" / "info_lobby_crew_1646-591-138-124.png"
GONE = 1.5  # seconds START must stay missing to count as gone


def run(appear=60, taps=3, delay=3, load=60, fade=20):
    """Return True once past the start screen, with the lobby showing or a popup
    open for the lobby routine to close; False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
        From launch it takes ~25 s (black, then a loading screen).
    taps: maximum taps on START.
    delay: seconds to wait for the start screen to go after each tap.
    load: seconds to wait for the lobby once the start screen has gone. The
        story loading screen after START took ~10 s.
    fade: seconds to wait for START once the start screen shows without it.
    The lobby wait (`load`) covers the ~20 s login after the tap too.
    """
    found = wait_until(_look, appear)
    if found is None:
        log.error(f"no start screen or lobby after {appear}s")
        return False
    state, screen = found
    if state != "start":
        return _report(state)

    if not locate(START_BUTTON, screen):
        log.debug("start screen without START, waiting")
        screen = wait_until(_with_start, fade)
    if screen is None:
        # The logo without START is also the game logging in after a tap
        # (any tap on this screen starts it), so carry on to the lobby.
        log.info(f"no START after {fade}s, game already starting")
        log.info("left start screen, waiting for lobby")
    tapped = 0
    while True:
        if screen is not None:
            if tapped == taps:
                log.error(f"START still showing after {taps} taps")
                return False
            tapped += 1
            x, y = tap(*locate(START_BUTTON, screen)[:2])
            log.debug(f"tap {tapped}/{taps} at ({x}, {y})")
            screen = _gone(delay + GONE)
            if screen is None:
                screen = _with_start()  # still up: tap again, or wait for it
                continue
            log.info("left start screen, waiting for lobby")
        found = wait_until(_after_tap, load)
        if found is None:
            log.error(f"no lobby {load}s after start screen")
            return False
        state, screen = found
        if state != "start":
            return _report(state)
        log.warning("START showing again, tap ignored")


def at_start_screen(screen=None):
    """True when the start screen is on screen (its logo shows), START or not."""
    screen = capture() if screen is None else screen
    return bool(locate(LOGO, screen))


def _with_start():
    """A fresh capture if START is on it, else None."""
    screen = capture()
    return screen if locate(START_BUTTON, screen) else None


def _state(screen):
    """"popup", "start", "lobby", or None for anything else."""
    from re1999.routines import lobby  # lobby imports this module
    if open_popup(lobby.popups(), screen):
        return "popup"
    if at_start_screen(screen):
        return "start"
    if locate(CREW, screen):
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
    """A fresh capture once START has been missing for GONE seconds in a row,
    or None if that doesn't happen within `timeout` seconds. START, not the
    logo: the logo stays up for ~20 s after the tap while the game logs in."""
    deadline = time.monotonic() + timeout
    since = None
    while time.monotonic() < deadline:
        screen = capture()
        if locate(START_BUTTON, screen):
            since = None
        else:
            since = since or time.monotonic()
            if time.monotonic() - since >= GONE:
                return screen
        time.sleep(0.2)
    return None


def _after_tap():
    """(state, screen) once the lobby, a popup or START shows, else None."""
    found = _look(("popup", "lobby"))
    if found:
        return found
    screen = _with_start()
    return None if screen is None else ("start", screen)

if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
