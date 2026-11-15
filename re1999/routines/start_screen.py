"""Get past the Reverse: 1999 start screen (title screen, START) into the lobby.

Usage: python -m re1999.routines.start_screen [--debug]

1. Wait for the start screen, the lobby, or a popup or lobby dialog to show
   (the game may still be loading, e.g. right after
   `python -m re1999.bot start`). Already in the lobby: done.
2. Tap START. Tap again if the start screen is still up after a moment.
3. Wait for the lobby (its Crew button) while the game loads.

The lobby counts only when no popup or lobby dialog is open: Crew matches
through the quit dialog's dim. On the first launch of the day the game shows
the obtained popup, then the check-in card and event-login, before the lobby.
Any of them is left open and the routine returns False; the lobby routine,
which hands over to this one, closes them and looks again.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import locate, open_popup
from re1999.config import TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
# Alpha-masked to its letters: an orbit spins across them.
START_BUTTON = START / "btn_start-screen_lobby_883-789-140-28.png"
CREW = START / "lobby" / "info_lobby_crew_1646-591-138-124.png"


def run(appear=60, taps=3, delay=3, load=60):
    """Return True once past the start screen and the lobby shows, False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
        From launch it takes ~25 s (black, then a loading screen).
    taps: maximum taps on START.
    delay: seconds to wait for the start screen to go after each tap.
    load: seconds to wait for the lobby once the start screen has gone. The
        story loading screen after START took ~10 s.
    """
    found = wait_until(_look, appear)
    if found is None:
        log.error(f"no start screen or lobby after {appear}s")
        return False
    state, screen = found
    if state != "start":
        return _report(state)

    for attempt in range(1, taps + 1):
        match = locate(START_BUTTON, screen)
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
    """True when the start screen is on screen (START shows)."""
    screen = capture() if screen is None else screen
    return bool(locate(START_BUTTON, screen))


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
        return False
    log.info("in lobby")
    return True


def _gone():
    screen = capture()
    return None if at_start_screen(screen) else screen


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
