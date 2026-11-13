"""Claim the daily shop: take the free product, then buy 40 Energy and 5 Flags for 100 green hearts each.

Usage: python -m e7.routines.claim_daily_shop [--debug]

1. Go to daily-shop (core.nav.goto).
2. Free: close any common popup, then look for Free over the whole screen.
   No Free means today's free product is already claimed: skip it. Otherwise
   tap Free until "Received Reward" shows, close it with "Tap to close", and
   check Free is gone.
3. 40 Energy, then 5 Flags: close any popup, find the card by its title over
   the whole screen, and look for the 100-heart pill below it. No pill means
   it's already bought today: skip it. Otherwise tap the pill until the Buy
   dialog shows, tap Buy until the dialog is gone, and check the pill is gone.
4. Go back to the lobby (the lobby routine).

A bought or claimed product moves to the end of the grid and shows a timer
instead of its price, so the grid's order changes from one claim to the next:
everything is looked for over the whole screen, never at a fixed spot.
"""

import sys

from core.log import logger, setup
from core.nav import close_popup, dialog, game_popups, goto, locate, open_popup, past_black, tap_until
from core.vision import find
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "daily-shop"
SHOP = TEMPLATES_DIR / "start-screen" / "lobby" / "main-menu" / "shop-landing" / MENU
FREE = SHOP / "btn_daily-shop_free_540-515-130-45_anywhere.png"
REWARD_TITLE = SHOP / "info_daily-shop_reward-title_770-222-380-60.png"  # "Received Reward"
REWARD_CLOSE = SHOP / "btn_daily-shop_reward-close_860-770-200-90.png"   # "Tap to close"
REWARD = dialog(REWARD_TITLE, REWARD_CLOSE)
PILL = SHOP / "btn_daily-shop_buy-100-hearts_540-515-130-45.png"         # heart + "100", cut on 40 Energy
BUY_TITLE = SHOP / "info_daily-shop_buy-title_890-205-140-65.png"        # "Buy"
BUY_CONFIRM = SHOP / "btn_daily-shop_buy-confirm_900-722-445-85.png"     # [heart 100] Buy
BUY = dialog(BUY_TITLE, BUY_CONFIRM)

# Products bought with green hearts: (title image, offset of the price pill's
# centre from the title match's centre). The pill sits 277 px below the title
# on every card; x differs because "40" is cut from the title's left end.
HEART_ITEMS = {
    "40 Energy": (SHOP / "info_daily-shop_energy-40_545-245-40-32_anywhere.png", (40, 277)),
    "5 Flags": (SHOP / "info_daily-shop_flags-5_1165-243-85-36_anywhere.png", (0, 277)),
}


def run(delay=1.5, tries=5):
    """Return True once the free product is claimed and every HEART_ITEMS
    product is bought, each now or earlier today, and the game is back in the
    lobby; False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = game_popups(GAME)
    if not _claim_free(popups, delay, tries):
        return False
    for name, (title, offset) in HEART_ITEMS.items():
        if not _buy(name, title, offset, popups, delay, tries):
            return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    log.info("done, back in lobby")
    return True


def _clear(popups, delay, tries):
    """The current screen with no common popup or shop dialog open, or None
    if one couldn't be closed. Rule 1: a dialog dims the grid, so the titles
    still match under it while Free and the pills don't."""
    known = {**popups, "reward": REWARD, "buy": BUY}
    screen = past_black()
    name = open_popup(known, screen)
    if name:
        if not close_popup(name, known[name], delay, tries):
            log.error(f"popup_{name} not closed")
            return None
        screen = past_black()
    return screen


def _claim_free(popups, delay, tries):
    screen = _clear(popups, delay, tries)
    if screen is None:
        return False
    if not locate(FREE, screen):
        log.info("Free: none showing, already claimed today")
        return True
    log.info("Free: claiming")
    if not tap_until(FREE, REWARD_TITLE, delay, tries, popups=popups):
        log.error("Free: Received Reward not shown")
        return False
    if not close_popup("reward", REWARD, delay, tries):
        log.error("Free: Received Reward not closed")
        return False
    if locate(FREE, past_black()):
        log.error("Free: still showing after the claim")
        return False
    log.info("Free: claimed")
    return True


def _pill(title, offset, screen):
    """Centre (x, y) of the 100-heart pill on `title`'s card, or None when the
    card isn't on screen or shows no pill (bought: a timer instead)."""
    card = locate(title, screen)
    if not card:
        return None
    x, y = card[0] + offset[0], card[1] + offset[1]
    return (x, y) if find(PILL, screen, (x - 65, y - 22, 130, 45)) else None


def _buy(name, title, offset, popups, delay, tries):
    screen = _clear(popups, delay, tries)
    if screen is None:
        return False
    if not locate(title, screen):
        log.error(f"{name}: card not on screen")
        return False
    pill = _pill(title, offset, screen)
    if not pill:
        log.info(f"{name}: no 100-heart price, already bought today")
        return True
    log.info(f"{name}: buying for 100 hearts")
    if not tap_until(pill, BUY_TITLE, delay, tries, popups=popups):
        log.error(f"{name}: Buy dialog not shown")
        return False
    if not close_popup("buy", BUY, delay, tries):
        log.error(f"{name}: Buy dialog not closed")
        return False
    if _pill(title, offset, past_black()):
        log.error(f"{name}: price still showing after Buy")
        return False
    log.info(f"{name}: bought")
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
