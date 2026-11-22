"""Get to the Arknights lobby from wherever the game is.

Usage: python -m ak.routines.lobby [--debug]

core.nav loads this module by name as the game's lobby routine, the start of
every menu walk, so keep its path and run() returning True on success.

Until the Squads tile shows with no popup or lobby dialog over it:
- if a stop screen (ak/templates/common/stops/) shows, give up without
  touching it: it waits on the user's choice, and a Back there could choose;
- while the screen is black or a known loading screen
  (ak/templates/common/loading/) shows, or the game started under LAUNCH
  seconds ago, wait; Back pressed then would be a guess;
- if one of the game's common popups (ak/templates/common/popups/) or a
  lobby dialog (DIALOGS) is open, close it and look again;
- if a start screen is up (pre-start or the title), hand over to the
  start_screen routine (and reset the Back count), at most HANDOVERS times;
- otherwise press Back.

Popups are checked before Squads (Rule 1), and closing one can open the next
(the sign-in calendar's reward, then the event boards), so the loop starts
over after each. Once the routine has acted (a Back, a close, a load, a
hand-over), Squads counts only after SETTLE seconds with no popup or dialog:
the login popups open ~1 s after the lobby is drawn (common: Lobbies), and a
Back pressed while a menu was closing opens quit late.

The lobby's HUD doesn't hide on its own, so there is nothing to wake.
"""

import sys

from core.device import uptime, wait_until
from core.input import back, capture
from core.log import logger, setup
from core.nav import (close_popup, dialog, game_popups, held, loading, locate, open_popup,
                      past_black, past_loading, stop_screen)
from ak.config import BACK_KEY, GAME, TEMPLATES_DIR
from ak.routines import start_screen

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
SQUADS = LOBBY / "info_lobby_squads_1050-465-185-80.png"
# For this long after the game's process starts, an unknown screen is a
# launch screen (the launch load's update checks, which show no image the
# bot knows: its "Clear Cache" button is on pre-start too) and the routine
# waits instead of pressing Back.
LAUNCH = 90  # seconds; launch to pre-start took ~30 s
SETTLE = 4  # seconds Squads must show with no popup once the routine has acted
# A start screen that keeps coming back after start_screen ran is one the
# routine can't get past (an error that loops to it): without a cap it would
# hand over forever, since each hand-over resets the Back count.
HANDOVERS = 3

DIALOGS = {
    # "Are you sure you want to exit?", opened by Back in the lobby. Its X
    # (Cancel), never the tick, which quits.
    "quit": dialog(LOBBY / "info_lobby_quit-text_735-465-450-48.png",
                   LOBBY / "btn_lobby_quit-cancel_630-706-72-72.png"),
    # "Leave the Base?", opened by Back on the base. Back cancels it, so a
    # Back loop toggles it forever; its tick leaves for the lobby.
    "leave-base": dialog(LOBBY / "base" / "info_base_leave-text_838-438-244-44.png",
                         LOBBY / "base" / "btn_base_lobby_1232-712-66-66.png"),
}


def popups():
    """The game's common popups and the lobby's dialogs, in the form core.nav
    takes, pre-start last: launch dialogs (voice settings) open over it and
    leave its diamond matching, so a dialog seen after it would never be
    closed, and every tap on the diamond would land on the dialog."""
    found = {**game_popups(GAME), **DIALOGS}
    return {**{k: v for k, v in found.items() if k != start_screen.PRE_START},
            start_screen.PRE_START: found[start_screen.PRE_START]}


def run(backs=10, delay=1.5):
    """Return True once the lobby is on screen with its HUD, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby, and maximum popups and
        dialogs closed.
    delay: seconds to keep checking the screen after each press or tap.
    """
    known = popups()
    screen = capture()
    presses = closed = handovers = settles = 0
    acted = False  # a Back, close, load or hand-over since the last look
    while True:
        screen = past_black(screen)
        stop = stop_screen(GAME, screen)
        if stop:
            log.error(f"stop_{stop} showing: the user's call, not acting on it")
            return False
        if loading(GAME, screen):
            screen = past_loading(GAME, screen)
            if screen is None:
                log.error("not reached, stuck on a loading screen")
                return False
            acted = True
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
            acted = True
            continue
        if locate(SQUADS, screen):
            if acted:
                if settles == backs:
                    log.error(f"lobby never held {SETTLE}s with no popup in {backs} looks")
                    return False
                settles += 1
                log.debug(f"squads showing, watching {SETTLE}s for popups")
                if held(lambda s: _clear_squads(s, known), SETTLE, SETTLE + delay) is None:
                    screen = capture()  # a popup opened, or Squads went: look again
                    continue
            log.info("reached")
            return True
        if start_screen.at_start_screen(screen):
            if handovers == HANDOVERS:
                log.error(f"start screen still showing after {HANDOVERS} hand-overs")
                return False
            handovers += 1
            log.info(f"start screen, handing over ({handovers}/{HANDOVERS})")
            start_screen.run(appear=delay)
            screen = capture()
            presses = 0
            acted = True
            continue
        age = uptime(GAME)
        if age is not None and age < LAUNCH:
            log.debug(f"game started {age}s ago, waiting")
            screen = wait_until(lambda: _known(capture(), known), LAUNCH - age)
            if screen is None:  # not `or`: a capture's truth value raises
                screen = capture()
            acted = True
            continue
        if presses == backs:
            log.error(f"not reached after {backs} backs")
            return False
        presses += 1
        log.debug(f"back {presses}/{backs}")
        back(BACK_KEY)
        acted = True
        screen = wait_until(_squads, delay)
        if screen is None:
            screen = capture()


def _clear_squads(screen, known):
    """`screen` if Squads shows on it with no popup or lobby dialog open, else None."""
    return screen if locate(SQUADS, screen) and not open_popup(known, screen) else None


def _known(screen, known):
    """`screen` if the routine knows what to do on it, else None."""
    if (stop_screen(GAME, screen) or loading(GAME, screen) or open_popup(known, screen)
            or locate(SQUADS, screen) or start_screen.at_start_screen(screen)):
        return screen
    return None


def _squads():
    """A fresh capture if Squads is on it, else None."""
    screen = capture()
    return screen if locate(SQUADS, screen) else None


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
