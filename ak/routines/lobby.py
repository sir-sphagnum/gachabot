"""Get to the Arknights lobby from wherever the game is: just launched, its
start screens, or any menu.

Usage: python -m ak.routines.lobby [--debug]

The loop is core.lobby's; this module holds Arknights' spec. core.nav loads
it by name as the game's lobby routine, the start of every menu walk, so
keep its path, run() and popups().

- Launch shows two start screens. pre-start (lore art over a yellow START
  diamond) is a common popup closed by its diamond, and is checked after
  every other popup: launch dialogs (voice settings) open over it and leave
  the diamond matching, so a dialog seen after it would never be closed.
  Then the title, its ARKNIGHTS logo over START.
- The lobby is the Squads tile. Its HUD doesn't hide on its own, so there
  is nothing to wake.
"""

import sys

from core.lobby import Lobby, StartScreen
from core.log import setup
from core.nav import dialog
from ak.config import BACK_KEY, GAME, TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
LOBBY = START / "lobby"

SPEC = Lobby(
    game=GAME,
    back_key=BACK_KEY,
    indicator=[LOBBY / "info_lobby_squads_1050-465-185-80.png"],
    start=StartScreen(
        identify=[START / "info_start-screen_logo_520-380-870-150.png"],  # START or not
        tap=START / "btn_start-screen_lobby_806-716-308-102.png",
        load=60,  # START to the lobby took ~12 s (Connecting, then the Rhodes Island load)
    ),
    dialogs={
        # "Are you sure you want to exit?", opened by Back in the lobby. Its X
        # (Cancel), never the tick, which quits.
        "quit": dialog(LOBBY / "info_lobby_quit-text_735-465-450-48.png",
                       LOBBY / "btn_lobby_quit-cancel_630-706-72-72.png"),
        # "Leave the Base?", opened by Back on the base. Back cancels it, so a
        # Back loop toggles it forever; its tick leaves for the lobby.
        "leave-base": dialog(LOBBY / "base" / "info_base_leave-text_838-438-244-44.png",
                             LOBBY / "base" / "btn_base_lobby_1232-712-66-66.png"),
    },
    last=("pre-start",),
    # The launch load's update checks show nothing the bot knows (its "Clear
    # Cache" button is on pre-start too). Launch to pre-start took ~30 s.
    launch=90,
    settle=4,  # the first login popup opened ~1 s after the lobby
)

run = SPEC.run
popups = SPEC.popups


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
