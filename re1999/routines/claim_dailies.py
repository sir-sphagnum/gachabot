"""Claim the Reverse: 1999 Daily Activeness task rewards, then go Home to the lobby.

Usage: python -m re1999.routines.claim_dailies [--debug]

Tasks may open on another tab, so the routine picks Daily Activeness first.
Matching is blind to brightness and the tab's label scores 0.90 chosen and
1.00 not, so a chosen tab is told by its orange fill, not by an image. Claim
All is the same art on every tab (0.98 on Weekly's), so it's only tapped once
Daily is chosen.

Claim All only shows while the tab has something to claim, so its absence
means done. It opens the common obtained popup; the tap runs with
popups=False, or tap_until would close that popup as an obstruction and keep
tapping Claim All instead of reporting it.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import close_popup, game_popups, goto, locate, tap_until
from core.vision import tint
from re1999.config import GAME, TEMPLATES_DIR

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
TASKS = LOBBY / "tasks"
DAILY_TAB = TASKS / "btn_tasks_daily-tab_1110-70-320-52.png"
CLAIM_ALL = TASKS / "btn_tasks_claim-all_1692-212-145-46.png"
HOME = TASKS / "btn_tasks_lobby_186-42-56-56.png"
CREW = LOBBY / "info_lobby_crew_1646-591-138-124.png"
OBTAINED = TEMPLATES_DIR / "common" / "popups" / "obtained" / "info_obtained_title_872-178-176-46.png"

# A strip of the Daily Activeness tab left of its label (x, y, w, h). Red
# minus blue there is ~149 with the tab chosen (orange) and 0 without (dark
# grey); the threshold sits halfway (common: Lit or grey).
TAB_BOX = (1080, 108, 30, 16)
CHOSEN_MIN = 75


def _daily_chosen(screen):
    return tint(screen, TAB_BOX, "r-b") >= CHOSEN_MIN


def _pick_daily(tries=5):
    """Tap the Daily Activeness tab until it's the chosen one."""
    return tap_until(DAILY_TAB, _daily_chosen, tries=tries) is not None


def run():
    """Return True once Daily Activeness has nothing left to claim and the lobby is up."""
    if not goto(GAME, "tasks"):
        log.error("tasks not reached")
        return False
    if not _pick_daily():
        log.error("daily activeness tab not chosen")
        return False
    if not locate(CLAIM_ALL, capture()):
        log.info("nothing to claim")
    else:
        if not tap_until(CLAIM_ALL, OBTAINED, popups=False):
            log.error("claim all opened no rewards")
            return False
        log.info("claimed, closing rewards")
        if not close_popup("obtained", game_popups(GAME)["obtained"]):
            log.error("rewards not closed")
            return False
    if not tap_until(HOME, CREW):
        log.error("lobby not reached")
        return False
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
