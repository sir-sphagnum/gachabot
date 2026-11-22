"""Get past the Arknights start screens (pre-start, then the title's START) into the lobby.

Usage: python -m ak.routines.start_screen [--debug]

Launch shows two start screens: pre-start (lore art over a yellow START
diamond, after the launch load's update checks), then the title (ARKNIGHTS
logo over a grey START).

1. Wait for pre-start, the title, the lobby, or a popup or lobby dialog to
   show (the game may still be loading, e.g. right after
   `python -m ak.bot start`). Already in the lobby: done.
2. Pre-start: tap its diamond until it goes (popup_pre-start), then wait for
   the title.
3. Title: tap START, waiting for it to fade in first if the title shows
   without it. Tap again if START is still up after a moment. START goes at
   the tap, while the logo stays ~1 s, so a logo whose START never fades in
   is a game already starting.
4. Wait for the lobby (its Squads tile) while the game loads. If START shows
   again meanwhile, the tap was ignored: tap again (step 3).

START counts as gone only once it has been missing for GONE seconds, so a
capture where it animates doesn't count as the tap taking (Rule 2).

The lobby counts only when no popup or lobby dialog is open (Rule 1). On the
first launch of the day the lobby shows for ~1 s, then the sign-in calendar,
its reward and the event boards open over it (common: Lobbies). Any of them
is left open and the routine returns True, its part done; the lobby routine,
which hands over to this one and runs after it, closes them and looks again.
A lobby seen with no popup is watched `settle` seconds more before the
routine returns, so the lobby routine run next can trust a lobby it finds
without having acted.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import close_popup, game_popups, held, locate, open_popup
from ak.config import GAME, TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
START_BUTTON = START / "btn_start-screen_lobby_806-716-308-102.png"
# The ARKNIGHTS logo marks the title screen, START or not.
LOGO = START / "info_start-screen_logo_520-380-870-150.png"
SQUADS = START / "lobby" / "info_lobby_squads_1050-465-185-80.png"
PRE_START = "pre-start"  # the popup that holds the pre-start screen's diamond
GONE = 1.5  # seconds START must stay missing to count as gone


def run(appear=120, taps=3, delay=3, load=60, fade=20, settle=5):
    """Return True once past the start screens, with the lobby showing or a
    popup open for the lobby routine to close; False otherwise.

    appear: seconds to wait for a start screen (or the lobby) to show up.
        From launch, pre-start took ~30 s; update checks and downloads on
        the launch load can make it longer.
    taps: maximum taps on START, and on the pre-start diamond.
    delay: seconds to wait for START to go after each tap.
    load: seconds to wait for the lobby once START has gone. It took ~12 s
        (the Connecting screen, then the Rhodes Island load).
    fade: seconds to wait for START once the title shows without it.
    settle: seconds to keep watching for a popup once the lobby shows. The
        first login popup opened ~1 s after the lobby.
    """
    pre_starts = 0
    while True:
        found = wait_until(_look, appear)
        if found is None:
            log.error(f"no start screen or lobby after {appear}s")
            return False
        state, screen = found
        if state != PRE_START:
            break
        if pre_starts == taps:
            log.error(f"pre-start still showing after {taps} closes")
            return False
        pre_starts += 1
        log.info("pre-start, tapping START")
        if not close_popup(PRE_START, game_popups(GAME)[PRE_START], delay, taps):
            log.error("pre-start not left")
            return False
    if state != "start":
        return _report(state, settle)

    if not locate(START_BUTTON, screen):
        log.debug("title without START, waiting")
        screen = wait_until(_with_start, fade)
    if screen is None:
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
            return _report(state, settle)
        log.warning("START showing again, tap ignored")


def at_start_screen(screen=None):
    """True when either start screen shows: pre-start's diamond, or the title's logo."""
    screen = capture() if screen is None else screen
    return bool(open_popup({PRE_START: game_popups(GAME)[PRE_START]}, screen)
                or locate(LOGO, screen))


def _with_start():
    """A fresh capture if START is on it, else None."""
    screen = capture()
    return screen if locate(START_BUTTON, screen) else None


def _state(screen):
    """PRE_START, "popup", "start", "lobby", or None for anything else."""
    from ak.routines import lobby  # lobby imports this module
    popup = open_popup(lobby.popups(), screen)
    if popup:
        return PRE_START if popup == PRE_START else "popup"
    if locate(LOGO, screen):
        return "start"
    if locate(SQUADS, screen):
        return "lobby"
    return None


def _look(states=(PRE_START, "popup", "start", "lobby")):
    """(state, screen) for a fresh capture if its state is one of `states`, else None."""
    screen = capture()
    state = _state(screen)
    return (state, screen) if state in states else None


def _report(state, settle):
    if state == "lobby":
        log.debug(f"lobby showing, watching {settle}s for popups")
        if wait_until(lambda: _look(("popup",)), settle):
            state = "popup"
    if state == "popup":
        log.info("popup open, returning to caller")
        return True
    log.info("in lobby")
    return True


def _gone(timeout):
    """A fresh capture once START has been missing for GONE seconds in a row,
    or None if that doesn't happen within `timeout` seconds."""
    return held(lambda screen: None if locate(START_BUTTON, screen) else screen, GONE, timeout)


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
