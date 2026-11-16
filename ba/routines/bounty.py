"""Spend every bounty ticket sweeping the last 3-starred Overpass stage.

Usage: python -m ba.routines.bounty [--debug]

1. Go to overpass (core.nav.goto: lobby > Campaign > Bounty > Overpass). Its
   stage list scrolls to the last stages on entry, so wait for it to settle.
2. If the ticket count is 0, nothing to do. Otherwise pick the lowest row
   whose stars are gold (the last stage cleared with 3 stars; rows below it
   have grey stars) and tap its Enter: Mission Info opens.
3. MAX, Start Sweep, Confirm on the "Use N Bounty Ticket" notice (it spends
   the tickets), then Confirm on Sweep Complete once its rewards have listed.
4. Close Mission Info (X), Home, then the lobby routine.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import goto, locate, settled, tap_until
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby, stage_sweep


log = logger(__file__)

MENU = "overpass"
OVERPASS = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / "bounty" / MENU
SETTLE = 5          # seconds to wait for the stage list to stop scrolling

# First digit of "Bounty Ticket N/6": 1.00 on 0, 0.42 on 21. Other counts
# weren't seen, hence the high threshold (as lesson's ticket digit).
ZERO = OVERPASS / "info_overpass_tickets-zero_414-278-24-36.png"
ZERO_MATCH = 0.95
# Enter's y on each row of the settled list (stages 06-10 when mapped), top
# to bottom.
ROWS = [357, 506, 655, 805, 954]
HOME = OVERPASS / "btn_overpass_lobby_1830-12-54-46.png"


def run(delay=1.5, tries=5):
    """Return True once no bounty ticket is left (or none was) and the game is
    back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not settled(SETTLE):
        log.debug(f"stage list still moving after {SETTLE}s, going on")
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
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
