"""Get to the E7 lobby with its HUD showing, from wherever the game is:
just launched, its start screen, or any menu.

Usage: python -m e7.routines.lobby [--debug]

The loop is core.lobby's; this module holds E7's spec. core.nav loads it by
name as the game's lobby routine, the start of every menu walk, so keep its
path, run() and popups().

- The start screen's copyright line is both its identifier and its START:
  any tap there starts the game (common: Tap anywhere). E7's loads are black.
- The lobby is the wall barrel with the main-menu icon. The barrel shows in
  every lobby state, so with the icon missing the lobby is at rest, and a
  tap on the icon's spot wakes its HUD. If the HUD was up and the tap opened
  the main-menu panel, the panel's X sits on the same spot, so the next tap
  closes it. The barrel still matches (0.96) through the quit dialog's dim
  and through "Disconnected from server", so popups are checked first.
- Patch Update's close is Proceed, which starts a download nothing is mapped
  on, so the loop waits for a known screen afterwards instead of pressing Back.
"""

import sys

from core.lobby import Idle, Lobby, StartScreen
from core.log import setup
from core.nav import dialog
from e7.config import BACK_KEY, GAME, TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
LOBBY = START / "lobby"
BARREL = LOBBY / "info_lobby_barrel_1240-140-80-120.png"  # scene: every state, day and night
MAIN_MENU = LOBBY / "btn_lobby_main-menu_1847-20-45-58.png"  # HUD: shows only when active
COPYRIGHT = START / "btn_start-screen_lobby_805-1023-311-26_white.png"

SPEC = Lobby(
    game=GAME,
    back_key=BACK_KEY,
    indicator=[BARREL, MAIN_MENU],
    start=StartScreen(identify=[COPYRIGHT], tap=COPYRIGHT, load=30),  # tap to lobby: ~7 s black load
    dialogs={
        # "Are you sure you want to quit the game?", and its Cancel.
        "quit": dialog(LOBBY / "info_lobby_quit-text_690-462-540-50.png",
                       LOBBY / "btn_lobby_lobby_660-650-280-80.png"),
        # "Rewards Received:", and its Confirm, which opens checkin-received.
        "checkin": dialog(LOBBY / "info_lobby_checkin-text_1420-882-260-44.png",
                          LOBBY / "btn_lobby_checkin-confirm_1530-965-170-60.png"),
        # "Received Check-In Reward", and its "Tap to close".
        "checkin-received": dialog(LOBBY / "info_lobby_checkin-received-title_675-170-570-65.png",
                                   LOBBY / "btn_lobby_checkin-received-close_860-1000-200-80.png"),
    },
    idle=Idle(identify=[BARREL], wake=(1869, 49)),  # the main-menu icon's centre
    launch=45,  # black, then the start screen within a few seconds
    settle=4,   # web-notice opened a few seconds after the lobby
    quiet_after={"patch-update": 300},  # an 18.4 MB patch took under 30 s
)

run = SPEC.run
popups = SPEC.popups


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
