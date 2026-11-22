"""Collect the Arknights base's products, orders and Trust, then go back to the lobby.

Usage: python -m ak.routines.base_collect [--debug]

Does three daily missions: "Collect Factory products", "Complete 1 orders"
and "Interact with Operators in the Base and increase their Trust" (both
tiers, 5 and 10: one Collect All gives 11).

1. Go to the base and open its notification bar (the bell, top right).
2. While one of Collectable, Orders Acquired or Trust is on the bar, tap it.
   Each claims at once (a toast says what it gave, no dialog) and leaves the
   bar, and the entries after it shift left into its slot, so each is
   found along the bar, not at a fixed spot.
3. The lobby routine: Back on the base opens "Leave the Base?", which it
   answers with the tick.

None of the three on the bar means each is claimed or has nothing to claim
yet, which counts as done (Rule 6).
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import clear, goto, tap_until
from core.vision import find
from ak.config import GAME, TEMPLATES_DIR
from ak.routines import lobby

log = logger(__file__)

MENU = "base"
BASE = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
BELL = BASE / "btn_base_notifications_1774-110-62-62_anywhere.png"  # the base view opens at varying zoom
BAR = BASE / "info_base_backlog-label_78-1022-96-44.png"  # "Backlog", left end of the bar
# Each label with its icon, not the count badge above it, which changes.
CLAIMS = {
    "collectable": BASE / "btn_base_collectable_312-1022-130-46_anywhere.png",
    "orders": BASE / "btn_base_orders_316-1028-126-34_anywhere.png",
    "trust": BASE / "btn_base_trust_348-1024-64-44_anywhere.png",
}
# Where the labels are searched: the bar's strip. Trust's label also scored
# 0.94 on the "Trust increased" toast at the top right.
STRIP = (180, 1000, 1740, 80)
GONE_WAIT = 4  # seconds for a tapped entry to leave the bar


def run(delay=1.5, tries=5):
    """Return True once the bar shows none of the three claims and the game
    is back in the lobby, False if it couldn't finish."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = lobby.popups()
    if not tap_until(BELL, BAR, delay, tries, popups=popups):
        log.error("notification bar not opened")
        return False
    for taps in range(tries + 1):
        screen = clear(popups, BAR, delay, tries)
        if screen is None:
            log.error("notification bar not usable")
            return False
        name, hit = _next_claim(screen)
        if not name:
            log.info("collected" if taps else "nothing to collect")
            break
        if taps == tries:
            log.error(f"{name} still on the bar after {tries} taps")
            return False
        x, y = tap(*hit[:2])
        log.debug(f"{name}: tap at ({x}, {y})")
        if not wait_until(lambda: not find(CLAIMS[name], capture(), STRIP), GONE_WAIT):
            log.warning(f"{name} still on the bar, looking again")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _next_claim(screen):
    """(name, match) of the leftmost claim on the bar, or (None, None)."""
    found = [(n, m) for n, t in CLAIMS.items() if (m := find(t, screen, STRIP))]
    return min(found, key=lambda f: f[1][0]) if found else (None, None)


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
