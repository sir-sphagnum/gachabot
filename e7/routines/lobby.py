"""Get to the E7 lobby with its HUD showing, from wherever the game is.

Usage: python -m e7.routines.lobby

Main loop: Look for barrel on screen, if no barrel not found, check if in start screen, if in start screen get start screen to routine to handle it, if not in start screen, press back.

If barrel is found, use tapuntil on the supposed location of the main menu icon in the lobby, until the main icon shows up

Quit game popup dialogue no longer matters, since pressing back gets rid of it al the same
"""

import sys

from core.device import wait_until
from core.input import back, capture, tap
from core.nav import close_popup, locate, open_popup
from core.tree import load_popups
from e7.config import BACK_KEY, GAME, TEMPLATES_DIR
from e7.routines import start_screen

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
BARREL = LOBBY / "info_lobby_barrel_1240-140-80-120.png"       # scene: both states, day and night
ACTIVE = [LOBBY / "btn_lobby_main-menu_1847-20-45-58.png",      # HUD: all must show
          LOBBY / "info_lobby_sanctuary_27-246-112-86.png"]
main_menu = (x,y) #coords of the main menu icon


def run(backs=10, taps=5, delay=1.5, verbose=True):
    """Return True once the active lobby is on screen, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby.
    taps: maximum taps to wake its HUD.
    delay: seconds to keep checking the screen after each press or tap.
    """
    say = print if verbose else (lambda *a: None)
   
    screen = capture()
    presses = 0
    while True:
       
        if locate(BARREL, screen):
           #use tapuntil on the x,y of the supposed main menu icon, until the main menu icon shows
           print('now in lobby')
           return True
        if start_screen.at_start_screen(screen):
            print('Game is in start screen')
            start_screen.run(appear=delay, verbose=verbose)
            screen = capture()
            presses = 0 #refresh back presses when at start screen
            continue
        if presses == backs:
            say(f"Lobby barrel not seen after {backs} Back presses")
            return False
        presses += 1
        say(f"Not in the lobby; Back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(lambda: _with(BARREL), delay) or capture()

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
