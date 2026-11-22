"""Get to the Blue Archive lobby from wherever the game is: just launched,
its start screen, or any menu.

Usage: python -m ba.routines.lobby [--debug]

The loop is core.lobby's; this module holds Blue Archive's spec. core.nav
loads it by name as the game's lobby routine, the start of every menu walk,
so keep its path, run() and popups().

- The start screen is told by its copyright line, which also shows on the
  title movie before Notice, Menu and TOUCH TO START do. Back there opens a
  quit dialog, so the loop waits for Notice and Menu, then taps TOUCH TO
  START, which pulses, as a point.
- The lobby is Campaign, part of the HUD. Neither news nor new-products
  covers it, so it still matches (1.00) under them. news shows ~2 s after
  Campaign does, then new-products when it closes.
- The idle lobby (HUD hidden, art zoomed in) ignores Back; a tap on the art
  brings the HUD back.
"""

import sys

from core.lobby import Idle, Lobby, StartScreen
from core.log import setup
from ba.config import BACK_KEY, GAME, TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
LOBBY = START / "lobby"
CAMPAIGN = LOBBY / "info_lobby_campaign_1728-996-156-46.png"  # the routines' Home taps wait for it

SPEC = Lobby(
    game=GAME,
    back_key=BACK_KEY,
    indicator=[CAMPAIGN],
    start=StartScreen(
        # The copyright line, its dark letters and their outline (alpha-masked):
        # it shows on the title movie too, which plays before Notice, Menu
        # and TOUCH TO START do.
        identify=[START / "info_start-screen_copyright_536-1028-850-32.png"],
        # Centre of "TOUCH TO START": its label pulses, so the point is tapped
        # rather than a match of btn_start-screen_lobby_795-918-330-42.png,
        # once Notice and Menu show.
        tap=(959, 940),
        ready=[START / "info_start-screen_notice_42-862-116-52.png",
               START / "info_start-screen_menu_42-930-110-54.png"],
        load=60,  # start screen to lobby took 8-23 s
    ),
    idle=Idle(
        # The hanging sign top right: 1.00 on three idle captures, at most 0.47 elsewhere.
        identify=[LOBBY / "info_lobby_rest-sign_1530-90-320-370.png"],
        wake=(1500, 600),  # a spot of the art with no HUD button under it
    ),
    launch=45,  # publisher logos and fades; launch to start screen took ~20 s
    settle=4,   # news shows ~2 s after Campaign
)

run = SPEC.run
popups = SPEC.popups


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
