"""Get to the Reverse: 1999 lobby from wherever the game is: just launched,
its start screen, or any menu.

Usage: python -m re1999.routines.lobby [--debug]

The loop is core.lobby's; this module holds Reverse: 1999's spec. core.nav
loads it by name as the game's lobby routine, the start of every menu walk,
so keep its path, run() and popups().

- The start screen is told by its logo, not by START, which fades in ~3 s
  after the screen and has an intro during which taps are ignored. After a
  tap the logo stays ~20 s while the game logs in, so a logo without START
  is waited on, never tapped or Backed.
- The lobby is the Crew button, part of the HUD. Crew still matches (1.00)
  through the quit dialog's dim, so the lobby's dialogs are checked first.
- Closing one dialog can open the next (the check-in card closes into its
  calendar, which closes into event-login).
"""

import sys

from core.lobby import Lobby, StartScreen
from core.log import setup
from core.nav import dialog
from re1999.config import BACK_KEY, GAME, TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
LOBBY = START / "lobby"
CREW = LOBBY / "info_lobby_crew_1646-591-138-124.png"  # other routines wait for it after Home
CORNER = (1870, 40)  # top-right corner of the screen, outside the check-in calendar

SPEC = Lobby(
    game=GAME,
    back_key=BACK_KEY,
    indicator=[CREW],
    start=StartScreen(
        # The "REVERSE 1999" logo, masked to its letters: it shows with START or without.
        identify=[START / "info_start-screen_logo_462-350-1000-182.png"],
        # Alpha-masked to its letters: an orbit spins across them.
        tap=START / "btn_start-screen_lobby_883-789-140-28.png",
        load=60,  # the story loading screen after START took ~10 s
    ),
    dialogs={
        # "Quit the Game?", opened by Back in the lobby. Cancel, never Confirm.
        "quit": dialog(LOBBY / "info_lobby_quit-text_584-496-172-38.png",
                       LOBBY / "btn_lobby_quit-cancel_1114-596-100-42.png"),
        # Daily sign-in card. Its calendar icon is the one control known to get
        # past it: it opens checkin-calendar, which the corner tap closes.
        "checkin": dialog(LOBBY / "info_lobby_checkin-text_864-542-188-40.png",
                          LOBBY / "btn_lobby_checkin-calendar_1094-70-92-62.png"),
        # The point, not the btn_ crop: that crop is blurred lobby, which changes.
        "checkin-calendar": dialog(LOBBY / "info_lobby_checkin-calendar-text_180-532-190-42.png",
                                   CORNER),
        # Player profile, which can show at login. The corner is outside its panels.
        "profile": dialog(LOBBY / "info_lobby_profile-detail_616-198-112-42.png", CORNER),
    },
    # Backs on the splash and the start screen's fade-in opened the quit
    # dialog. Launch to the start screen took ~20 s.
    launch=45,
    settle=3,
)

run = SPEC.run
popups = SPEC.popups


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
