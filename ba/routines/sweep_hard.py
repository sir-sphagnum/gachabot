"""Sweep the Hard stages of the Multi-Sweep preset as many times as allowed.

Usage: python -m ba.routines.sweep_hard [--debug]

1. Go to mission (core.nav.goto: lobby > Campaign > Mission) and open
   Multi-Sweep. Whatever preset tab it opens on is used, with its ticked
   stages as they are.
2. If the yellow Multi-Sweep button is grey, today's counts are used up:
   nothing to do. Otherwise tap MAX, Multi-Sweep, Confirm on Sweep Content
   (it spends AP), then Confirm on Sweep Complete.
3. Close Multi-Sweep (X), Home, then the lobby routine.
"""

import sys
import time

from core.input import capture, tap
from core.log import logger, setup
from core.nav import close_popup, dialog, goto, locate, tap_until
from core.vision import load
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby

log = logger(__file__)

MENU = "mission"
MISSION = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / MENU
OPEN = MISSION / "btn_mission_multi-sweep_712-860-182-44.png"
# Not the "Multi-Sweep" title: mission toasts slide over it after a sweep
# (0.67). "Selection List" sits below them.
SELECTION_LIST = MISSION / "info_mission_selection-list_166-324-186-44.png"
CLOSE = MISSION / "btn_mission_multi-sweep-close_1808-126-50-50.png"
MAX = MISSION / "btn_mission_sweep-max_1174-856-108-64.png"
SWEEP = MISSION / "btn_mission_sweep-start_1546-862-246-50.png"
# Yellow vs grey Multi-Sweep: the template scores 0.91 on the grey button,
# so tell them apart by colour. Mean red minus mean blue over the button is
# +139 yellow and -2 grey (count 0, every stage used up).
SWEEP_AREA = (slice(862, 912), slice(1550, 1790))
YELLOW = 60
CONTENT_TITLE = MISSION / "info_mission_sweep-content-title_784-126-352-56.png"
CONTENT_CONFIRM = MISSION / "btn_mission_sweep-confirm_980-832-344-94.png"
# "Final Rewards Earned": the title is under the toasts too.
COMPLETE = MISSION / "info_mission_sweep-complete-final_304-686-234-82.png"
COMPLETE_CONFIRM = MISSION / "btn_mission_complete-confirm_784-820-354-110.png"
SWEEP_DELAY = 3     # the sweep took ~2 s before Sweep Complete showed
MAX_WAIT = 1        # seconds for the count to update after MAX
HOME = MISSION / "btn_mission_lobby_1830-12-54-46.png"


def run(delay=1.5, tries=5):
    """Return True once the preset is swept (or was already today) and the
    game is back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not tap_until(OPEN, SELECTION_LIST, delay, tries):
        log.error("multi-sweep not opened")
        return False
    if _yellow(capture()):
        if not _sweep(delay, tries):
            return False
    else:
        log.info("already swept today, nothing to do")
    if not close_popup("multi-sweep", dialog(SELECTION_LIST, CLOSE), delay, tries):
        log.error("multi-sweep not closed")
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _sweep(delay, tries):
    match = locate(MAX, capture())
    if match:
        tap(*match[:2])
        time.sleep(MAX_WAIT)  # let the count and AP bubble update
    else:
        log.warning("MAX not found, sweeping the count as it is")
    if not tap_until(SWEEP, CONTENT_TITLE, delay, tries):
        log.error("sweep content not shown")
        return False
    log.info("sweeping")
    if not tap_until(CONTENT_CONFIRM, COMPLETE, SWEEP_DELAY, tries):
        log.error("sweep complete not shown")
        return False
    if not tap_until(COMPLETE_CONFIRM, SELECTION_LIST, delay, tries):
        log.error("sweep complete not closed")
        return False
    if _yellow(capture()):
        log.warning("multi-sweep still yellow after the sweep: counts left")
    log.info("swept")
    return True


def _yellow(screen):
    b, _, r = load(screen)[SWEEP_AREA].reshape(-1, 3).mean(axis=0)
    return r - b > YELLOW


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
