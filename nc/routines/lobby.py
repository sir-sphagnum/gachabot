"""Get to the Neural Cloud lobby from wherever the game is.

Usage: python -m nc.routines.lobby [--debug]

core.nav loads this module by name as the game's lobby routine, the start of
every menu walk, so keep its path and run() returning True on success.

Until the Explore title shows with no popup or lobby dialog over it:
- while the screen is black or the loading screen (LOADING) shows, or the
  game started under LAUNCH seconds ago, wait; Back pressed then would be a
  guess;
- if one of the game's common popups (nc/templates/common/popups/) or the
  quit dialog is open, close it (CANCEL, never CONFIRM) and look again;
- if the start screen is up, hand over to the start_screen routine (and
  reset the Back count);
- otherwise press Back.

Popups and the quit dialog are checked before the Explore title, which still
matches through their dim. Closing one can uncover another (login-reward
closes into monthly-signin), so the loop starts over after each.

The Explore title is part of the HUD, which stays up while idle, so the lobby
counts as reached only with its HUD up.
"""

import sys

from core.device import uptime, wait_until
from core.input import back, capture
from core.log import logger, setup
from core.nav import close_popup, dialog, game_popups, locate, open_popup, past_black
from nc.config import BACK_KEY, GAME, TEMPLATES_DIR
from nc.routines import start_screen

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
EXPLORE = LOBBY / "info_lobby_explore-title_1316-290-212-64.png"
# Loading screens: nothing on them answers Back, so the routine waits them out.
LOADING = [TEMPLATES_DIR / "common" / "loading" / "info_loading_resources-text_88-1002-228-30.png"]
LOAD_WAIT = 60  # seconds; the launch load took ~8 s
# For this long after the game's process starts, an unknown screen is a launch
# screen (splash, fades) and the routine waits instead of pressing Back.
LAUNCH = 30  # seconds; launch to start screen took ~12 s

DIALOGS = {
    # "Are you sure you want to quit the game?", opened by Back in the lobby.
    # CANCEL, never CONFIRM.
    "quit": dialog(LOBBY / "info_lobby_quit-text_568-502-432-36.png",
                   LOBBY / "btn_lobby_cancel_1176-598-92-38.png"),
}


def popups():
    """The game's common popups and the lobby's dialogs, in the form core.nav takes."""
    return {**game_popups(GAME), **DIALOGS}


def run(backs=10, delay=1.5):
    """Return True once the lobby is on screen with its HUD, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby, and maximum popups and
        dialogs closed.
    delay: seconds to keep checking the screen after each press or tap.
    """
    known = popups()
    screen = capture()
    presses = closed = 0
    while True:
        screen = past_black(screen)
        if loading(screen):
            log.debug("loading screen, waiting")
            screen = wait_until(lambda: _unless(loading, capture()), LOAD_WAIT)
            if screen is None:
                log.error(f"still loading after {LOAD_WAIT}s")
                return False
            continue
        popup = open_popup(known, screen)
        if popup:
            if closed == backs:
                log.error(f"popups still showing after closing {backs}")
                return False
            closed += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, known[popup], delay):
                log.error(f"popup_{popup} not closed")
                return False
            screen = capture()
            continue
        if locate(EXPLORE, screen):
            log.info("reached")
            return True
        if start_screen.at_start_screen(screen):
            log.info("start screen, handing over")
            start_screen.run(appear=delay)
            screen = capture()
            presses = 0
            continue
        age = uptime(GAME)
        if age is not None and age < LAUNCH:
            log.debug(f"game started {age}s ago, waiting")
            screen = wait_until(lambda: _known(capture(), known), LAUNCH - age)
            if screen is None:  # not `or`: a capture's truth value raises
                screen = capture()
            continue
        if presses == backs:
            log.error(f"not reached after {backs} backs")
            return False
        presses += 1
        log.debug(f"back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(_explore, delay)
        if screen is None:
            screen = capture()


def loading(screen):
    """True when one of the game's loading screens shows."""
    return any(locate(t, screen) for t in LOADING)


def _known(screen, known):
    """`screen` if the routine knows what to do on it, else None."""
    if (loading(screen) or open_popup(known, screen) or locate(EXPLORE, screen)
            or start_screen.at_start_screen(screen)):
        return screen
    return None


def _unless(check, screen):
    """`screen` unless check(screen) is true, else None (for wait_until)."""
    return None if check(screen) else screen


def _explore():
    """A fresh capture if the Explore title is on it, else None."""
    screen = capture()
    return screen if locate(EXPLORE, screen) else None


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
