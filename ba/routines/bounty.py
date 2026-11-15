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
import time

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import close_popup, dialog, goto, locate, past_black, tap_until
from core.vision import difference, fingerprint, load
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby

import cv2

log = logger(__file__)

MENU = "overpass"
OVERPASS = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / "bounty" / MENU
SETTLE = 5          # seconds to wait for the stage list to stop scrolling
STILL = 1.0         # percent of changed pixels below which the list is still

# First digit of "Bounty Ticket N/6": 1.00 on 0, 0.42 on 21. Other counts
# weren't seen, hence the high threshold (as lesson's ticket digit).
ZERO = OVERPASS / "info_overpass_tickets-zero_414-278-24-36.png"
ZERO_MATCH = 0.95
# Enter's y on each row of the settled list (stages 06-10 when mapped), top
# to bottom; Enter sits at x 1676 on every row.
ROWS = [357, 506, 655, 805, 954]
ENTER_X = 1676
# The row's three stars sit left of its name, 10-38 px below Enter's centre.
# Mean red minus blue over them: +62 gold, -5 grey.
STARS_X = slice(1042, 1116)
STARS_DY = (10, 38)
GOLD = 30

INFO_TITLE = OVERPASS / "info_overpass_mission-info-title_824-186-274-52.png"
INFO_CLOSE = OVERPASS / "btn_overpass_mission-info-close_1664-184-54-54.png"
MAX = OVERPASS / "btn_overpass_sweep-max_1568-420-108-64.png"
MAX_WAIT = 1        # seconds for the count to update after MAX
SWEEP = OVERPASS / "btn_overpass_sweep-start_1272-586-266-50.png"
# The notice's Confirm: the same button as the cafe's invite Confirm (1.00),
# trusted only because Start Sweep was just tapped.
NOTICE_CONFIRM = OVERPASS / "btn_overpass_sweep-confirm_976-708-348-100.png"
# "Final Rewards Earned": shows once the per-sweep rewards have listed (a few
# seconds for 21 sweeps). The title is under mission toasts.
COMPLETE = OVERPASS / "info_overpass_sweep-complete-final_302-682-238-86.png"
COMPLETE_DELAY = 3
COMPLETE_TRIES = 8
COMPLETE_CONFIRM = OVERPASS / "btn_overpass_sweep-done_788-822-346-106.png"
HOME = OVERPASS / "btn_overpass_lobby_1830-12-54-46.png"


def run(delay=1.5, tries=5):
    """Return True once no bounty ticket is left (or none was) and the game is
    back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    _settle()
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
    y = _last_three_star(capture())
    if y is None:
        log.error("no 3-starred stage on screen")
        return False
    if not tap_until((ENTER_X, y), INFO_TITLE, delay, tries):
        log.error("mission info not opened")
        return False
    match = locate(MAX, capture())
    if match:
        tap(*match[:2])
        time.sleep(MAX_WAIT)  # let the count and ticket bubble update
    else:
        log.warning("MAX not found, sweeping the count as it is")
    if not tap_until(SWEEP, NOTICE_CONFIRM, delay, tries):
        log.error("sweep notice not shown")
        return False
    log.info("sweeping")
    if not tap_until(NOTICE_CONFIRM, COMPLETE, COMPLETE_DELAY, COMPLETE_TRIES):
        log.error("sweep complete not shown")
        return False
    if not tap_until(COMPLETE_CONFIRM, INFO_TITLE, delay, tries):
        log.error("sweep complete not closed")
        return False
    if not close_popup("mission-info", dialog(INFO_TITLE, INFO_CLOSE), delay, tries):
        log.error("mission info not closed")
        return False
    if not _no_tickets():
        log.warning("tickets left after the sweep")
    log.info("swept")
    return True


def _last_three_star(screen):
    """Enter's y on the lowest row with gold stars, or None."""
    img = load(screen)
    for y in reversed(ROWS):
        b, _, r = img[y + STARS_DY[0]:y + STARS_DY[1], STARS_X].reshape(-1, 3).mean(axis=0)
        if r - b > GOLD:
            log.debug(f"3-starred row at y {y} (r-b {r - b:.0f})")
            return y
    return None


def _settle():
    """Wait until two captures in a row barely differ (the list stopped)."""
    last = [_print(past_black())]

    def still():
        now = _print(capture())
        moved = difference(last[0], now)
        last[0] = now
        return moved < STILL

    if not wait_until(still, SETTLE, interval=0.3):
        log.debug(f"stage list still moving after {SETTLE}s, going on")


def _print(screen):
    return fingerprint(cv2.cvtColor(load(screen), cv2.COLOR_BGR2GRAY))


def _no_tickets():
    return bool(locate(ZERO, capture(), ZERO_MATCH))


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
