"""Collect the day's credit in the Arknights Credit Store, then go back to the lobby.

Usage: python -m ak.routines.claim_credit [--debug]

Does the daily mission "Collect Credit from the Credit Store 1 time(s)".

1. Go to the Credit Store (Store, then its Credit Store tab).
2. While Claim (top right, next to the credit count) is orange, tap it. It
   opens the common resource-gained popup, which core.nav.clear closes on
   the next round, and turns grey ("Collected").
3. The lobby routine.

Grey means collected today, which counts as done (Rule 6). Nothing here is
bought: the store's items are tapped by nothing.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import clear, goto, open_popup
from core.vision import tint
from ak.config import GAME, TEMPLATES_DIR
from ak.routines import lobby

log = logger(__file__)

MENU = "credit-store"
TAB = (TEMPLATES_DIR / "start-screen" / "lobby" / "store" / MENU
       / "info_credit-store_credit-store-tab_1736-140-140-44.png")

# Claim is tapped as a point and read lit or grey by colour (common: Lit or
# grey). Mean red minus blue over the box is 180 orange "Claim", 0 grey
# "Collected" (2026-11-22).
CLAIM = (1460, 46, 140, 30)
ORANGE = 90
CLAIM_WAIT = 5  # seconds for the reward popup to show, or Claim to go grey


def run(delay=1.5, tries=5):
    """Return True once Claim is grey and the game is back in the lobby,
    False if it couldn't finish."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = lobby.popups()
    for taps in range(tries + 1):
        screen = clear(popups, TAB, delay, tries)
        if screen is None:
            log.error(f"{MENU} not usable")
            return False
        if not _orange(screen):
            log.info("collected" if taps else "already collected")
            break
        if taps == tries:
            log.error(f"claim still orange after {tries} taps")
            return False
        x, y = tap(CLAIM[0] + CLAIM[2] // 2, CLAIM[1] + CLAIM[3] // 2)
        log.debug(f"claim: tap {taps + 1}/{tries} at ({x}, {y})")
        # The popup closes on the next round, in clear.
        wait_until(lambda: open_popup(popups, s := capture()) or not _orange(s), CLAIM_WAIT)
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _orange(screen):
    return tint(screen, CLAIM, "r-b") > ORANGE


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
