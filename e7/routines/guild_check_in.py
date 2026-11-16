"""Check in at the guild: enter the guild hall, then go back to the lobby.

Usage: python -m e7.routines.guild_check_in [--debug]

1. Go to guild (core.nav.goto: lobby > main-menu > guild). Entering the hall
   is the check-in; the hall's "Check-Ins: n/4" counts the guild's members
   who have checked in.
2. Go back to the lobby (the lobby routine). It closes the game's common
   popups and presses Back on any screen it doesn't know, so a dialog the
   guild opens on entry is dismissed on the way out.

The dialog the guild may show on entry hasn't been captured, so nothing here
identifies it. If it hides the guild title, goto's first walk fails and its
second walk starts from the lobby (Back closes the dialog, then leaves the
guild) and enters the hall again.
"""

import sys

from core.log import logger, setup
from core.nav import goto
from e7.config import GAME
from e7.routines import lobby

log = logger(__file__)

MENU = "guild"


def run():
    """Return True once the guild hall was reached and the game is back in
    the lobby; False if either failed."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    log.info("checked in")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
