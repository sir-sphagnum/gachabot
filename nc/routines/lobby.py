"""Get to the Project Neural Cloud lobby from wherever the game is: just
launched, its start screen, or any menu.

Usage: python -m nc.routines.lobby [--debug]

The loop is core.lobby's; this module holds Neural Cloud's spec. core.nav
loads it by name as the game's lobby routine, the start of every menu walk,
so keep its path, run() and popups().

- The start screen's copyright line also shows on the System Self-Check load
  after START (0.94). The loop checks loads before the start screen, so the
  self-check template must stay in common/loading/.
- The lobby's HUD doesn't hide on its own, so there is nothing to wake.
"""

import sys

from core.lobby import Lobby, StartScreen
from core.log import setup
from core.nav import dialog
from nc.config import BACK_KEY, GAME, TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
LOBBY = START / "lobby"

SPEC = Lobby(
    game=GAME,
    back_key=BACK_KEY,
    indicator=[LOBBY / "info_lobby_explore_1316-286-214-72.png",
               LOBBY / "info_lobby_achievement_1304-780-160-40.png"],
    start=StartScreen(
        identify=[START / "info_start-screen_copyright_790-1036-340-36.png"],  # START or not
        tap=START / "btn_start-screen_lobby_672-862-576-62.png",
        load=30,  # START to the lobby took ~4 s (Connecting, then the self-check load)
    ),
    dialogs={
        # "Are you sure you want to quit the game?", opened by Back in the
        # lobby. CANCEL, never CONFIRM, which quits.
        "quit": dialog(LOBBY / "info_lobby_quit-text_568-502-432-38.png",
                       LOBBY / "btn_lobby_quit-cancel_1174-598-96-40.png"),
    },
    # Login Reward opens over the calendar, whose title still matches under
    # its dim, so the calendar's X would land on Login Reward.
    last=("monthly-signin",),
    launch=45,  # launch to the start screen took ~10 s
    settle=4,  # the announcement opened ~1 s after the lobby
)

run = SPEC.run
popups = SPEC.popups


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
