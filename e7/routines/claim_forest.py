"""Collect the Forest of Souls: claim each grower that is ready and use Cultivate while it's lit.

Usage: python -m e7.routines.claim_forest [--debug]

1. Go to forest-of-souls (core.nav.goto).
2. For Penguin Nest, Spirit Well and MolaGora Farm, in that order: when the row
   shows "Receive Reward", tap it until the reward dialog opens, then tap its
   "Tap to close" until it's gone. A row showing a timer isn't ready: skip it.
3. While Cultivate is lit, tap it once and wait for its count to change.
   Grey means no uses left: skip it.
4. Go back to the lobby (the lobby routine).

Before reading the menu, it closes any common popup or reward dialog and
checks the menu's title, since a dialog dims the rows (Receive Reward drops
from 1.0 to 0.16) while the title still matches through it.
"""

import sys

import numpy as np

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import (close_popup, dialog, game_popups, goto, locate, open_popup, past_black,
                      tap_until)
from core.vision import find, load
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "forest-of-souls"
FOREST = TEMPLATES_DIR / "start-screen" / "lobby" / "sanctuary" / MENU
TITLE = FOREST / "info_forest-of-souls_title_98-26-260-52.png"
RECEIVE = FOREST / "btn_forest-of-souls_receive-reward_1468-378-186-36.png"  # cropped on Penguin Nest's row
RECEIVE_BOX = (1468, 378, 186, 36)
CLOSE = FOREST / "btn_forest-of-souls_reward-close_860-765-200-90.png"
CULTIVATE = FOREST / "btn_forest-of-souls_cultivate_1622-810-155-48.png"

# Each row's offset below Penguin Nest's. The rows share one layout, so a ready
# row shows the same "Receive Reward" text, shifted down. MolaGora Farm's offset
# comes from its label (y 705 vs 359); it hasn't been seen ready yet.
ROWS = {"penguin-nest": 0, "spirit-well": 174, "molagora-farm": 347}

# Each reward dialog has its own title (it names the reward), but "Tap to close"
# sits in the same place on all of them, so it both identifies and closes them.
REWARD = dialog(CLOSE, CLOSE)

# Lit vs grey Cultivate: the template scores 0.96 on the grey button, so tell
# them apart by colour. Mean green minus mean blue over the button is +41 lit
# and -12 grey.
BUTTON = (slice(805, 860), slice(1610, 1850))
LIT = 15
COUNT = (slice(815, 855), slice(1775, 1840))  # the "(2/3)" text
CHANGED = 5  # mean pixel difference of COUNT: 0 between captures of one count, 30 from 2/3 to 3/3
MAX_USES = 3


def run(delay=1.5, tries=5, settle=5):
    """Return True once every ready row is claimed, Cultivate is grey (or
    used MAX_USES times) and the game is back in the lobby, False if it
    couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    settle: seconds to wait for Cultivate's count to change after a tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = {**game_popups(GAME), "reward": REWARD}
    for row, dy in ROWS.items():
        if not _claim(row, dy, popups, delay, tries):
            return False
    if not _cultivate(popups, delay, tries, settle):
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _claim(row, dy, popups, delay, tries):
    screen = _clear(popups, delay, tries)
    if screen is None:
        return False
    x, y, w, h = RECEIVE_BOX
    match = find(RECEIVE, screen, (x, y + dy, w, h))
    if not match:
        log.info(f"{row}: not ready, skipping")
        return True
    log.info(f"{row}: ready, claiming")
    if not tap_until(match[:2], CLOSE, delay, tries):
        log.error(f"{row}: reward dialog not shown")
        return False
    if not close_popup("reward", REWARD, delay, tries):
        log.error(f"{row}: reward dialog not closed")
        return False
    log.info(f"{row}: claimed")
    return True


def _cultivate(popups, delay, tries, settle):
    for use in range(1, MAX_USES + 1):
        screen = _clear(popups, delay, tries)
        if screen is None:
            return False
        if not _lit(screen):
            log.info("cultivate: grey, done" if use > 1 else "cultivate: grey, skipping")
            return True
        before = _count(screen)
        log.info(f"cultivate: lit, using {use}/{MAX_USES}")
        match = locate(CULTIVATE, screen)
        if not match:
            log.error("cultivate: button not found")
            return False
        # One tap, never retried: a second tap before the count updates would
        # spend another use.
        x, y = tap(*match[:2])
        log.debug(f"cultivate: tap at ({x}, {y})")
        if not wait_until(lambda: _changed(_count(capture()), before), settle):
            log.error(f"cultivate: count unchanged {settle}s after tap")
            return False
    log.info(f"cultivate: used {MAX_USES}, done")
    return True


def _clear(popups, delay, tries):
    """The current screen once no popup or reward dialog is open and the menu's
    title shows, or None (logged) if that can't be had."""
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
    b, g, _ = load(screen)[BUTTON].reshape(-1, 3).mean(axis=0)
    return g - b > LIT


def _count(screen):
    return load(screen)[COUNT].astype(int)


def _changed(count, before):
    return np.abs(count - before).mean() > CHANGED


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
