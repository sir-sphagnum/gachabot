"""Buy Covenant Bookmarks and Mystic Medals in the secret shop, refreshing it for skystones only when asked.

Usage: python -m e7.routines.refresh_secret_shop [--refresh N] [--debug]

1. Go to secret-shop (core.nav.goto).
2. Scan the item list: swipe it back to the top, look for each item's icon
   down the icon column, then swipe up once (that reaches the end of the
   six-row list) and look again. For each item found whose row Buy is still lit, tap Buy until the
   buy dialog's own Buy shows, tap that until the dialog is gone, and check
   the row's Buy went grey (bought: 0/1).
3. --refresh N: N times, tap Refresh until "Use Skystone to refresh?"
   shows, tap Confirm until it's gone (3 skystones each), and scan again.
   Without it, no skystones are spent.
4. Go back to the lobby (the lobby routine).
"""

import sys
import time

import cv2

from core.device import wait_until
from core.input import capture, swipe
from core.log import logger, setup
from core.nav import close_popup, dialog, game_popups, goto, locate, open_popup, past_black, tap_until
from core.vision import find
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "secret-shop"
SHOP = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
TITLE = SHOP / "info_secret-shop_title_100-25-205-55.png"                # "Secret Shop", identifies the menu
# Items to buy, found by their icon (without the count under it). Rows move
# as the list scrolls, so each icon is searched down the whole icon column,
# ICON_COLUMN, not at its file's box. Not over the whole screen: the same
# icons show in reward windows (orbis-guide's reward 1.00, auto's complete
# 0.99), and an _anywhere info_ would identify secret-shop there.
ITEMS = [
    ("Covenant Bookmarks", SHOP / "info_secret-shop_covenant-bookmarks-icon_845-912-115-95.png"),
    ("Mystic Medals", SHOP / "info_secret-shop_mystic-medals-icon_845-362-115-95.png"),
]
ICON_COLUMN = (830, 100, 145, 980)
REFRESH = SHOP / "btn_secret-shop_refresh_340-965-125-50.png"
REFRESH_QUESTION = SHOP / "info_secret-shop_refresh-question_795-462-330-50.png"
REFRESH_CONFIRM = SHOP / "btn_secret-shop_refresh-confirm_1060-665-125-52.png"
# The buy dialog's green Buy tells the dialog is open: its "Buy" title also
# shows on daily-shop's buy dialog, and an info_ would identify secret-shop.
BUY_CONFIRM = SHOP / "btn_secret-shop_buy-confirm_1180-740-100-52.png"
# Dialogs left open close with Cancel; the routine's own taps answer them
# with Buy or Confirm (close_popup taps the "close" until the info is gone).
OPEN_DIALOGS = {
    "buy": dialog(BUY_CONFIRM, SHOP / "btn_secret-shop_buy-cancel_665-740-115-50.png"),
    "refresh": dialog(REFRESH_QUESTION, SHOP / "btn_secret-shop_refresh-cancel_745-665-115-52.png"),
}
BUY = dialog(BUY_CONFIRM, BUY_CONFIRM)
REFRESH_DIALOG = dialog(REFRESH_QUESTION, REFRESH_CONFIRM)

# Every row's Buy sits at x 1785, 46 px below its icon's centre.
BUY_X, BUY_DY = 1785, 46
# A row's Buy is lit while it can be bought: green minus blue over
# (1725, Buy y - 30, 125, 60) is +27..+29 lit, +12 bought (0/1), +4 under a
# dialog's dim. The icon still matches on a bought row (0.96).
BUY_BOX = (1725, -30, 125, 60)   # x, y offset from the Buy's centre, w, h
LIT_MIN = 20
# The swipe that scrolls the list: up over its middle reaches the end of six
# rows (326 px of travel); the reverse goes back to the top.
LIST_DOWN = (1200, 850, 1200, 300)
LIST_UP = (1200, 300, 1200, 850)
SWIPE_SETTLE = 1.5   # seconds the list keeps moving after a swipe
SETTLE = 5           # seconds after Buy for the row to go grey


def run(refreshes=0, delay=1.5, tries=5):
    """Return True once each list seen (the current one, then one per
    refresh) has had its wanted items bought, and the game is back in the
    lobby; False if it couldn't finish.

    refreshes: how many times to refresh the list, for 3 skystones each.
    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = game_popups(GAME)
    if not _scan(ITEMS, popups, delay, tries):
        return False
    for n in range(1, refreshes + 1):
        log.info(f"refresh {n}/{refreshes}, 3 skystones")
        if not _refresh(popups, delay, tries):
            return False
        if not _scan(ITEMS, popups, delay, tries):
            return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    log.info("done, back in lobby")
    return True


def _clear(popups, delay, tries):
    """The current screen on secret-shop with no popup or shop dialog open,
    or None. Rule 1: the shop's title and the item titles still match under
    the dialogs' dim."""
    known = {**popups, **OPEN_DIALOGS}
    screen = past_black()
    name = open_popup(known, screen)
    if name:
        log.warning(f"popup_{name} open, closing")
        if not close_popup(name, known[name], delay, tries):
            log.error(f"popup_{name} not closed")
            return None
        screen = past_black()
    if not locate(TITLE, screen):
        log.error(f"{MENU} not on screen")
        return None
    return screen


def _swipe(points):
    swipe(*points)
    time.sleep(SWIPE_SETTLE)


def _buy_y(icon, screen):
    """y of the Buy on `icon`'s row, or None when the item isn't showing."""
    hit = find(icon, screen, ICON_COLUMN, margin=0)
    return hit[1] + BUY_DY if hit else None


def _lit(screen, y):
    x, dy, w, h = BUY_BOX
    b, g, _ = cv2.mean(screen[y + dy:y + dy + h, x:x + w])[:3]
    return g - b >= LIT_MIN


def _scan(items, popups, delay, tries):
    """Buy every wanted item on the list, top half then bottom half. True
    once both halves were looked at."""
    seen = set()
    for half, points in (("top", LIST_UP), ("bottom", LIST_DOWN)):
        _swipe(points)
        for name, icon in items:
            if name in seen:
                continue
            screen = _clear(popups, delay, tries)
            if screen is None:
                return False
            y = _buy_y(icon, screen)
            if y is None:
                continue
            seen.add(name)
            if not _lit(screen, y):
                log.info(f"{name}: already bought")
                continue
            if not _buy(name, icon, y, popups, delay, tries):
                return False
    for name, _ in items:
        if name not in seen:
            log.info(f"{name}: not on the list")
    return True


def _buy(name, icon, y, popups, delay, tries):
    """Buy the item whose row's Buy is at y."""
    log.info(f"{name}: buying")
    if not tap_until((BUY_X, y), BUY_CONFIRM, delay, tries, popups=popups):
        log.error(f"{name}: buy dialog not shown")
        return False
    if not close_popup("buy", BUY, delay, tries):
        log.error(f"{name}: buy dialog not closed")
        return False

    def bought():
        screen = capture()
        row = _buy_y(icon, screen)
        return row is not None and not _lit(screen, row)

    if not wait_until(bought, SETTLE):
        log.error(f"{name}: Buy still lit {SETTLE}s after buying")
        return False
    log.info(f"{name}: bought")
    return True


def _refresh(popups, delay, tries):
    """Tap Refresh and Confirm its dialog. True once the dialog is gone and
    the shop shows again (the new list starts at the top)."""
    screen = _clear(popups, delay, tries)
    if screen is None:
        return False
    if not tap_until(REFRESH, REFRESH_QUESTION, delay, tries, popups=popups):
        log.error("refresh dialog not shown")
        return False
    # Confirm is also the lobby quit dialog's Confirm (1.00 there):
    # close_popup taps it only while the question shows.
    if not close_popup("refresh", REFRESH_DIALOG, delay, tries):
        log.error("refresh dialog not closed")
        return False
    if _clear(popups, delay, tries) is None:
        return False
    log.info("refreshed")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    setup(debug="--debug" in args)
    n = int(args[args.index("--refresh") + 1]) if "--refresh" in args else 0
    sys.exit(0 if run(refreshes=n) else 1)
