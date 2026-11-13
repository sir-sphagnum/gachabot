"""Get past the E7 start screen (title screen, "Tap to Start") into the lobby.

Usage: python -m e7.routines.start_screen [--debug]

1. Wait for the start screen, the lobby, or one of the game's common popups
   to show (the game may still be loading, e.g. right after
   `python -m e7.bot start`). Already in the lobby: done.
2. Tap the "(c) Smilegate. All Rights Reserved." line at the bottom; it marks
   the start screen and starts the game like any tap does. Tap again if the
   start screen is still up after a moment.
3. Wait for the lobby (its wall barrel) while the game loads.

The lobby counts only when no common popup is open: some show over the lobby
with the barrel still matching through the dim. A popup is left open and the
routine returns False; the lobby routine, which hands over to this one, closes
it and looks again.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import game_popups, locate, open_popup
from e7.config import GAME, TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
COPYRIGHT = START / "btn_start-screen_lobby_805-1023-311-26_white.png"
BARREL = START / "lobby" / "info_lobby_barrel_1240-140-80-120.png"


def run(appear=60, taps=3, delay=3, load=30):
    """Return True once past the start screen and the lobby shows, False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
    taps: maximum taps on the start screen.
    delay: seconds to wait for the start screen to go after each tap.
    load: seconds to wait for the lobby once the start screen has gone.
    """
    found = wait_until(_look, appear)
    if found is None:
        log.error(f"no start screen or lobby after {appear}s")
        return False
    state, screen = found
    if state != "start":
        return _report(state)

    for attempt in range(1, taps + 1):
        match = locate(COPYRIGHT, screen)
        if not match:
            break
        x, y = tap(*match[:2])
        log.debug(f"tap {attempt}/{taps} at ({x}, {y})")
        screen = wait_until(_gone, delay)
        if screen is None:
            screen = capture()
    if at_start_screen(screen):
        log.error(f"still on start screen after {taps} taps")
        return False

    log.info("left start screen, waiting for lobby")
    found = wait_until(lambda: _look(("popup", "lobby")), load)
    if found is None:
        log.error(f"no lobby {load}s after start screen")
        return False
    return _report(found[0])


def at_start_screen(screen=None):
    """True when the start screen is on screen (its copyright line shows)."""
    screen = capture() if screen is None else screen
    return bool(locate(COPYRIGHT, screen))


def _state(screen):
    """"popup", "start", "lobby", or None for anything else."""
    if open_popup(game_popups(GAME), screen):
        return "popup"
    if at_start_screen(screen):
        return "start"
    if locate(BARREL, screen):
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
        return False
    log.info("in lobby")
    return True


def _gone():
    screen = capture()
    return None if at_start_screen(screen) else screen


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
