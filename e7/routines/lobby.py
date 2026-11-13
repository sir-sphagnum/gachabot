"""Get to the E7 lobby with its HUD showing, from wherever the game is.

Usage: python -m e7.routines.lobby [--debug]

core.nav loads this module by name as E7's lobby routine, the start of every
menu walk, so keep its path and run() returning True on success.

1. Until the lobby's wall barrel shows with no popup or lobby dialog over it:
   - while the screen is black (the game loading), wait; Back pressed then
     would be a guess;
   - if one of the game's common popups (e7/templates/common/popups/) or a
     lobby dialog (quit, daily check-in, check-in received) is open, close it
     (Cancel for the quit dialog) and look again;
   - if the start screen is up, hand over to the start_screen routine (and
     reset the Back count);
   - otherwise press Back.
2. Once the barrel shows, tap the main-menu icon's spot (top right) with
   core.nav.tap_until until the icon itself shows, which means the HUD is up.

Popups and the quit dialog are checked before the barrel because some show
over the lobby with the barrel still matching through the dim: the quit
dialog (opened when Back is pressed once too many in the lobby) and
"Disconnected from server", which leads to the start screen once closed.
Closing one can change where the game is, so the loop starts over after each.

If the HUD is at rest and the tap opens the main-menu panel, the panel's X
sits on the same spot, so the next tap closes it and the HUD stays up.
"""

import sys

from core.device import wait_until
from core.input import back, capture
from core.log import logger, setup
from core.nav import (close_popup, dialog, game_popups, locate, open_popup, past_black,
                      tap_until)
from e7.config import BACK_KEY, GAME, TEMPLATES_DIR
from e7.routines import start_screen

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
BARREL = LOBBY / "info_lobby_barrel_1240-140-80-120.png"     # scene: every state, day and night
MAIN_MENU = LOBBY / "btn_lobby_main-menu_1847-20-45-58.png"  # HUD: shows only when active
MAIN_MENU_SPOT = (1869, 49)  # centre of MAIN_MENU's box
QUIT = dialog(LOBBY / "info_lobby_quit-text_690-462-540-50.png",  # "Are you sure you want to quit the game?"
              LOBBY / "btn_lobby_lobby_660-650-280-80.png")    # its Cancel button
CHECKIN = dialog(LOBBY / "info_lobby_checkin-text_1420-882-260-44.png",  # "Rewards Received:"
                 LOBBY / "btn_lobby_checkin-confirm_1530-965-170-60.png")  # Confirm, opens CHECKIN_RECEIVED
CHECKIN_RECEIVED = dialog(LOBBY / "info_lobby_checkin-received-title_675-170-570-65.png",
                          LOBBY / "btn_lobby_checkin-received-close_860-1000-200-80.png")  # "Tap to close"


def run(backs=10, taps=5, delay=1.5):
    """Return True once the active lobby is on screen, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby, and maximum popups and
        quit dialogs closed.
    taps: maximum taps to wake its HUD.
    delay: seconds to keep checking the screen after each press or tap.
    """
    popups = {**game_popups(GAME), "quit": QUIT,
              "checkin": CHECKIN, "checkin-received": CHECKIN_RECEIVED}
    screen = capture()
    presses = closed = 0
    while True:
        screen = past_black(screen)
        popup = open_popup(popups, screen)
        if popup:
            if closed == backs:
                log.error(f"popups still showing after closing {backs}")
                return False
            closed += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, popups[popup], delay):
                log.error(f"popup_{popup} not closed")
                return False
            screen = capture()
            continue
        if locate(BARREL, screen):
            break
        if start_screen.at_start_screen(screen):
            log.info("start screen, handing over")
            start_screen.run(appear=delay)
            screen = capture()
            presses = 0
            continue
        if presses == backs:
            log.error(f"not reached after {backs} backs")
            return False
        presses += 1
        log.debug(f"back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(lambda: _with(BARREL), delay) or capture()

    log.info("reached, waking HUD")
    if tap_until(MAIN_MENU_SPOT, MAIN_MENU, delay, taps, popups=popups):
        log.info("HUD showing")
        return True
    log.error("HUD not shown")
    return False


def _with(template):
    """A fresh capture if `template` is on it, else None."""
    screen = capture()
    return screen if locate(template, screen) else None


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
