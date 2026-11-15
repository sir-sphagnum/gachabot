"""Sweeping a stage from a ticket stage list (bounty, scrimmage).

Both lists open the same Mission Info dialog, Notice and Sweep Complete, in
the same places: the images mapped on bounty's overpass score 1.00 on
scrimmage's gehenna captures, so only overpass keeps them. Their rows share a
layout too (Enter at x 1676, stars 10-38 px below it). Not a routine: bounty
and scrimmage call it.
"""

import time

from core.input import capture, tap
from core.log import logger
from core.nav import close_popup, dialog, locate, tap_until
from core.vision import load
from ba.config import TEMPLATES_DIR

log = logger(__file__)

OVERPASS = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / "bounty" / "overpass"

ENTER_X = 1676
# A row's three stars sit left of its name, 10-38 px below Enter's centre.
# Mean red minus blue over them: +62/+64 gold, -5 to +6 grey (overpass, gehenna).
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


def last_three_star(screen, rows):
    """Enter's y on the lowest of `rows` (Enter ys, top to bottom) whose stars
    are gold, or None."""
    img = load(screen)
    for y in reversed(rows):
        b, _, r = img[y + STARS_DY[0]:y + STARS_DY[1], STARS_X].reshape(-1, 3).mean(axis=0)
        if r - b > GOLD:
            log.debug(f"3-starred row at y {y} (r-b {r - b:.0f})")
            return y
    return None


def sweep(y, delay, tries):
    """Open the row whose Enter is at y, sweep it MAX times (every ticket),
    close the results and Mission Info. True once back on the stage list."""
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
    return True
