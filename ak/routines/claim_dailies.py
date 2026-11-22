"""Claim the Arknights daily missions' rewards (common: Daily missions), then go back to the lobby.

Usage: python -m ak.routines.claim_dailies [--debug]

1. Go to Missions. It opens on Pinboard (or another tab with rewards
   waiting), so tap the Daily tab until it shows chosen: dark, where the
   others are light grey. Chosen and not score 0.09-0.14 on each other.
2. While the "Collect All" banner tops the list, tap it. It claims every
   finished row at once and opens the common resource-gained popup; the tap
   runs with popups=False so tap_until reports that popup instead of
   closing it as an obstruction (common: Reward dialogs).
3. The lobby routine.

The banner shows only while a row waits to be claimed, so its absence means
done (Rule 6). A claim can bring a row's next tier (Trust 5, then 10), which
may already be complete: the loop looks again after each claim.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import clear, close_popup, game_popups, goto, locate, tap_until
from ak.config import GAME, TEMPLATES_DIR
from ak.routines import lobby

log = logger(__file__)

MENU = "missions"
MISSIONS = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
DAILY_TAB = MISSIONS / "btn_missions_daily-tab_1014-18-294-72.png"  # not chosen
DAILY_CHOSEN = MISSIONS / "info_missions_daily-chosen_1014-18-294-72.png"
COLLECT_ALL = MISSIONS / "btn_missions_collect-all_1482-130-390-102.png"
GAINED = (TEMPLATES_DIR / "common" / "popups" / "resource-gained"
          / "info_resource-gained_title_840-214-240-48.png")


def run(delay=1.5, tries=5):
    """Return True once the Daily tab has nothing left to claim and the lobby is up."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = lobby.popups()
    if not tap_until(DAILY_TAB, DAILY_CHOSEN, delay, tries, popups=popups):
        log.error("daily tab not chosen")
        return False
    for claims in range(tries + 1):
        screen = clear(popups, DAILY_CHOSEN, delay, tries)
        if screen is None:
            log.error("daily tab not usable")
            return False
        if not locate(COLLECT_ALL, screen):
            log.info("claimed" if claims else "nothing to claim")
            break
        if claims == tries:
            log.error(f"collect all still showing after {tries} claims")
            return False
        if not tap_until(COLLECT_ALL, GAINED, delay, tries, popups=False):
            log.error("collect all opened no rewards")
            return False
        log.info("claimed, closing rewards")
        if not close_popup("resource-gained", game_popups(GAME)["resource-gained"]):
            log.error("rewards not closed")
            return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
