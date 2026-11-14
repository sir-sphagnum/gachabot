"""Claim the Orbis Guide's daily reputation chest: tap the 100 chest while its badge is lit.

Usage: python -m e7.routines.claim_dailies [--debug]

1. Go to orbis-guide (core.nav.goto). It opens on Three Sisters' Diary, the
   tab with the reputation bar and its chests at 10, 20, 30, 50, 80 and 100.
2. Close any common popup or reward dialog, and check the menu's title.
3. If the 100 chest's orange badge isn't lit, there is nothing to claim
   (already claimed, or under 100 points): done.
4. Tap the 100 chest until "Reputation Point Rewards" shows. One tap claims
   every ready chest on the bar, not just this one.
5. Close the dialog with "Tap to close", then go back to the lobby (the lobby
   routine).
"""

import sys

from core.log import logger, setup
from core.nav import close_popup, dialog, game_popups, goto, locate, open_popup, past_black, tap_until
from core.vision import load
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "orbis-guide"
GUIDE = TEMPLATES_DIR / "start-screen" / "lobby" / "main-menu" / MENU
TITLE = GUIDE / "info_orbis-guide_title_98-95-235-60.png"
CHEST = GUIDE / "btn_orbis-guide_chest-100_1742-124-60-60.png"
REWARD_TITLE = GUIDE / "info_orbis-guide_reward-title_685-222-550-62.png"  # "Reputation Point Rewards"
# "Tap to close" also scores 0.96-0.99 on the other menus' reward dialogs, so
# the dialog is told by its title, not by this button.
REWARD_CLOSE = GUIDE / "btn_orbis-guide_reward-close_860-750-200-90.png"
REWARD = dialog(REWARD_TITLE, REWARD_CLOSE)

# The chest image matches the same with or without its badge under a dim, so
# lit is told by colour: mean red minus blue over the badge is +205 lit and
# -4..+5 on every other capture (claimed under the reward dialog, main-menu).
BADGE = (slice(113, 127), slice(1729, 1743))
LIT = 100


def run(delay=1.5, tries=5):
    """Return True once the chests are claimed, or the 100 chest has no badge
    (nothing to claim), and the game is back in the lobby; False if it
    couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = {**game_popups(GAME), "reward": REWARD}
    screen = _clear(popups, delay, tries)
    if screen is None:
        return False
    if _lit(screen):
        log.info("chest-100: badge lit, claiming")
        # The reward dialog is left out of tap_until's popups: it is what
        # the tap is waiting for, not something in the way.
        if not tap_until(CHEST, REWARD_TITLE, delay, tries, popups=game_popups(GAME)):
            log.error("Reputation Point Rewards not shown")
            return False
        if not close_popup("reward", REWARD, delay, tries):
            log.error("Reputation Point Rewards not closed")
            return False
        log.info("chests claimed")
    else:
        log.info("chest-100: no badge, nothing to claim")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _clear(popups, delay, tries):
    """The current screen once no popup or reward dialog is open and the menu's
    title shows, or None (logged) if that can't be had. The title still
    matches under the reward dialog's and the date-changed popup's dim, so
    popups are closed first (Rule 1)."""
    for _ in range(tries + 1):
        screen = past_black()
        popup = open_popup(popups, screen)
        if not popup:
            if locate(TITLE, screen):
                return screen
            log.error(f"left {MENU}")
            return None
        log.warning(f"popup_{popup} open, closing")
        if not close_popup(popup, popups[popup], delay, tries):
            log.error(f"popup_{popup} not closed")
            return None
    log.error(f"popups still showing after closing {tries}")
    return None


def _lit(screen):
    b, _, r = load(screen)[BADGE].reshape(-1, 3).mean(axis=0)
    return r - b > LIT


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
