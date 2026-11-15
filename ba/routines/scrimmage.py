"""Spend every scrimmage ticket sweeping the last 3-starred Gehenna stage.

Usage: python -m ba.routines.scrimmage [--debug]

1. Go to gehenna (core.nav.goto: lobby > Campaign > Scrimmage > Gehenna).
2. If the ticket count is 0, nothing to do. Otherwise pick the lowest row
   whose stars are gold and sweep it MAX times (ba.routines.stage_sweep).
   Each sweep costs 1 ticket and 10 AP.
3. Home, then the lobby routine.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import goto, locate, tap_until
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby, stage_sweep

log = logger(__file__)

MENU = "gehenna"
GEHENNA = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / "scrimmage" / MENU

# First digit of "Tickets Owned N/6": 1.00 on 0, 0.46 on 7. Other counts
# weren't seen, hence the high threshold (common: Reading a zero).
ZERO = GEHENNA / "info_gehenna_tickets-zero_430-278-20-36.png"
ZERO_MATCH = 0.95
# Enter's y on each row (stages 01-04), top to bottom. The list has four
# rows and doesn't scroll.
ROWS = [279, 429, 578, 728]
HOME = GEHENNA / "btn_gehenna_lobby_1830-12-54-46.png"


def run(delay=1.5, tries=5):
    """Return True once no scrimmage ticket is left (or none was) and the
    game is back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if _no_tickets():
        log.info("no tickets left, nothing to do")
    elif not _sweep(delay, tries):
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _sweep(delay, tries):
    y = stage_sweep.last_three_star(capture(), ROWS)
    if y is None:
        log.error("no 3-starred stage on screen")
        return False
    if not stage_sweep.sweep(y, delay, tries):
        return False
    if not _no_tickets():
        log.warning("tickets left after the sweep")
    log.info("swept")
    return True


def _no_tickets():
    return bool(locate(ZERO, capture(), ZERO_MATCH))


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
