"""Claim Background Battling: open it from the HUD clock, Calculate, and close it.

Usage: python -m e7.routines.claim_auto [--debug]

1. Get to the active lobby (the lobby routine).
2. If the HUD shows no clock, there is nothing to claim: done. The clock shows
   only while a background battle has rewards waiting.
3. Tap the clock until the auto menu ("Background Battling") opens.
4. Tap Calculate until "Calculation Complete" shows. No Calculate on auto is
   a failure.
5. Close Calculation Complete with "Tap to close"; auto then shows Close.
6. Tap Close until the lobby's main-menu icon shows.

The clock is tapped right after the lobby routine wakes the HUD, since the
lobby falls back to rest within seconds. tap_until locates the clock before
each tap, so a tap that only wakes a resting HUD is followed by one on the
clock.
"""

import sys

from core.log import logger, setup
from core.nav import game_popups, locate, open_popup, past_black, tap_until
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

COMMON = TEMPLATES_DIR / "common"
AUTO = COMMON / "auto"
CLOCK = COMMON / "hud" / "btn_hud_auto_1388-12-72-68.png"
TITLE = AUTO / "info_auto_title_778-76-366-58.png"                    # "Background Battling"
CALCULATE = AUTO / "btn_auto_calculate_780-908-370-70.png"
COMPLETE_TITLE = AUTO / "info_auto_complete-title_726-156-468-64.png"  # "Calculation Complete"
COMPLETE_CLOSE = AUTO / "btn_auto_complete-close_860-835-200-95.png"   # "Tap to close"
CLOSE = AUTO / "btn_auto_close_780-908-370-70.png"


def run(delay=1.5, tries=5, attempts=2):
    """Return True once the rewards are claimed and the lobby is back, or the
    HUD shows no clock (nothing to claim); False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    attempts: times to get the lobby's HUD up and look for the clock.
    """
    popups = game_popups(GAME)
    for attempt in range(1, attempts + 1):
        if not lobby.run():
            log.error("lobby not reached")
            return False
        screen = past_black()
        # Rule 1: a popup over the lobby can hide the HUD; the lobby routine
        # closes it on the next attempt.
        if open_popup(popups, screen):
            continue
        if locate(CLOCK, screen):
            break
        if locate(lobby.MAIN_MENU, screen):
            log.info("no clock on the HUD, nothing to claim")
            return True
        log.debug(f"HUD not showing, attempt {attempt}/{attempts}")
    else:
        log.error(f"HUD not seen in {attempts} attempts")
        return False

    log.info("clock showing, opening auto")
    if not tap_until(CLOCK, TITLE, delay, tries, popups=popups):
        log.error("auto not opened")
        return False
    if not locate(CALCULATE, past_black()):
        log.error("auto shows no Calculate")
        return False
    if not tap_until(CALCULATE, COMPLETE_TITLE, delay, tries, popups=popups):
        log.error("Calculation Complete not shown")
        return False
    log.info("calculated, closing")
    if not tap_until(COMPLETE_CLOSE, CLOSE, delay, tries, popups=popups):
        log.error("Calculation Complete not closed")
        return False
    if not tap_until(CLOSE, lobby.MAIN_MENU, delay, tries, popups=popups):
        log.error("auto not closed")
        return False
    log.info("claimed, back in lobby")
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
