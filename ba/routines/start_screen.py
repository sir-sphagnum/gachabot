"""Get past the Blue Archive start screen (title screen, "TOUCH TO START") into the lobby.

Usage: python -m ba.routines.start_screen [--debug]

1. Wait for the start screen, the lobby, or one of the game's common popups
   to show (the game may still be loading, e.g. right after
   `python -m ba.bot start`). Already in the lobby: done.
2. Tap where "TOUCH TO START" shows. The label pulses, so it is tapped as a
   point, and the start screen is told by its Notice and Menu buttons. Tap
   again if the start screen is still up after a moment.
3. Wait for the lobby (its Campaign label) through the "Now Loading" screens,
   then a few seconds more for a popup to show over it.

The lobby counts only when no common popup is open: Campaign still matches
with the news and new-products popups over the lobby. A popup is left open
and the routine returns True, its part done; the lobby routine, which hands
over to this one and runs after it, closes it and looks again.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import game_popups, locate, open_popup
from ba.config import GAME, TEMPLATES_DIR

log = logger(__file__)

START = TEMPLATES_DIR / "start-screen"
NOTICE = START / "info_start-screen_notice_42-862-116-52.png"
MENU = START / "info_start-screen_menu_42-930-110-54.png"
# Centre of "TOUCH TO START". Its label pulses, so the point is tapped
# rather than a match of btn_start-screen_lobby_795-918-330-42.png.
TOUCH_TO_START = (959, 940)
CAMPAIGN = START / "lobby" / "info_lobby_campaign_1728-996-156-46.png"


def run(appear=60, taps=3, delay=3, load=60, settle=6):
    """Return True once past the start screen, with the lobby showing or a popup
    open for the lobby routine to close; False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
    taps: maximum taps on the start screen.
    delay: seconds to wait for the start screen to go after each tap.
    load: seconds to wait for the lobby once the start screen has gone. The
        "Now Loading" screens took ~10 s.
    settle: seconds to keep watching for a popup once the lobby has loaded.
    """
    found = wait_until(_look, appear)
    if found is None:
        log.error(f"no start screen or lobby after {appear}s")
        return False
    state, screen = found
    if state != "start":
        return _report(state)

    for attempt in range(1, taps + 1):
        x, y = tap(*TOUCH_TO_START)
        log.debug(f"tap {attempt}/{taps} at ({x}, {y})")
        screen = wait_until(_gone, delay)
        if screen is not None:
            break
    else:
        log.error(f"still on start screen after {taps} taps")
        return False

    log.info("left start screen, waiting for lobby")
    found = wait_until(lambda: _look(("popup", "lobby")), load)
    if found is None:
        log.error(f"no lobby {load}s after start screen")
        return False
    if found[0] == "lobby":
        # The news popup shows ~2 s after Campaign does, so a lobby seen
        # right after the load isn't popup-free yet.
        log.debug(f"lobby showing, watching {settle}s for popups")
        if wait_until(lambda: _look(("popup",)), settle):
            return _report("popup")
    return _report(found[0])


def at_start_screen(screen=None):
    """True when the start screen is on screen (Notice and Menu show)."""
    screen = capture() if screen is None else screen
    return bool(locate(NOTICE, screen)) and bool(locate(MENU, screen))


def _state(screen):
    """"popup", "start", "lobby", or None for anything else."""
    if open_popup(game_popups(GAME), screen):
        return "popup"
    if at_start_screen(screen):
        return "start"
    if locate(CAMPAIGN, screen):
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


def _gone():
    screen = capture()
    return None if at_start_screen(screen) else screen


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
