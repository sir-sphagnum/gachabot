"""Get to the E7 lobby with its HUD showing, from wherever the game is.

Usage: python -m e7.routines.lobby

1. Until the lobby's wall barrel shows: if the start screen is up, hand over
   to the start_screen routine (and reset the Back count); otherwise press
   Back.
2. Once the barrel shows, tap the main-menu icon's spot (top right) with
   core.nav.tap_until until the icon itself shows, which means the HUD is up.

The quit dialog ("Are you sure you want to quit the game?") opens when Back
is pressed once too many in the lobby. The lobby, barrel included, shows
dimmed behind it, so step 1 ends with the dialog still up. tap_until cancels
it before tapping, as it is one of the game's common popups.

If the HUD is at rest and the tap opens the main-menu panel, the panel's X
sits on the same spot, so the next tap closes it and the HUD stays up.
"""

import sys

from core.device import wait_until
from core.input import back, capture
from core.nav import locate, tap_until
from e7.config import BACK_KEY, TEMPLATES_DIR
from e7.routines import start_screen

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
BARREL = LOBBY / "info_lobby_barrel_1240-140-80-120.png"     # scene: both states, day and night
MAIN_MENU = LOBBY / "btn_lobby_main-menu_1847-20-45-58.png"  # HUD: shows only when active
MAIN_MENU_SPOT = (1869, 49)  # centre of MAIN_MENU's box


def run(backs=10, taps=5, delay=1.5, verbose=True):
    """Return True once the active lobby is on screen, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby.
    taps: maximum taps to wake its HUD.
    delay: seconds to keep checking the screen after each press or tap.
    """
    say = print if verbose else (lambda *a: None)

    screen = capture()
    presses = 0
    while not locate(BARREL, screen):
        if start_screen.at_start_screen(screen):
            say("On the start screen; handing over to start_screen")
            start_screen.run(appear=delay, verbose=verbose)
            screen = capture()
            presses = 0
            continue
        if presses == backs:
            say(f"Lobby barrel not seen after {backs} Back presses")
            return False
        presses += 1
        say(f"Not in the lobby; Back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(lambda: _with(BARREL), delay) or capture()

    say("In the lobby; waking the HUD")
    if tap_until(MAIN_MENU_SPOT, MAIN_MENU, delay, taps, popups=True, verbose=verbose):
        say("Lobby is active")
        return True
    say(f"Lobby HUD not shown after {taps} taps")
    return False


def _with(template):
    """A fresh capture if `template` is on it, else None."""
    screen = capture()
    return screen if locate(template, screen) else None


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
