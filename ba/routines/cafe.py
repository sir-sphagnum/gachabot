"""Claim the cafe's earnings and invite the student with the highest relationship rank.

Usage: python -m ba.routines.cafe [--debug]

1. Go to the cafe (core.nav.goto), and close the Guide / Visiting Student
   List dialog if it opens (Confirm).
2. Earnings: open Cafe Earnings; while Claim is yellow, tap it and close the
   reward popup it opens. Grey means nothing to claim. Close the dialog (X).
3. Invite: if the Invitation ticket is available (pink, not grey with a
   cooldown), open it, sort by Relationship Rank unless the sort button
   already reads so, tap Invite on the first row and Confirm.
4. Back to the lobby: Home icon, then the lobby routine.

Only the cafe the game opens on (No. 1) is handled; Move to Cafe No. 2 isn't
mapped yet.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import (clear, close_popup, dialog, game_popups, goto, locate, open_popup,
                      past_black, tap_until)
from core.vision import tint
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby

log = logger(__file__)

MENU = "cafe"
CAFE = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
TITLE = CAFE / "info_cafe_title_158-14-92-46.png"
HOME = CAFE / "btn_cafe_lobby_1830-12-54-46.png"

GUIDE = dialog(CAFE / "info_cafe_guide-title_820-360-282-46.png",
               CAFE / "btn_cafe_guide-confirm_792-636-338-104.png")
GUIDE_WAIT = 3  # seconds to watch for the guide after the cafe shows

EARNINGS = CAFE / "btn_cafe_earnings_1668-950-196-36.png"
EARNINGS_TITLE = CAFE / "info_cafe_earnings-title_806-196-310-54.png"
CLAIM = CAFE / "btn_cafe_earnings-claim_796-742-330-100.png"
EARNINGS_CLOSE = CAFE / "btn_cafe_earnings-close_1446-194-56-56.png"
# Yellow vs grey Claim: the template scores 0.86 on the grey button, so tell
# them apart by colour. Mean red minus mean blue over the button is +165
# yellow and 0 grey.
CLAIM_AREA = (800, 750, 320, 90)
YELLOW = 60
CLAIM_WAIT = 5  # seconds for the reward popup to show after Claim

# The pink ticket. It turns grey with a cooldown once used, and then the
# template doesn't match at all.
INVITATION = CAFE / "btn_cafe_invitation_1270-940-112-98.png"
INVITATION_TIP = CAFE / "info_cafe_invitation-tip_708-920-598-40.png"
SORT = CAFE / "btn_cafe_invitation-sort_998-200-186-56.png"
SORTED = CAFE / "info_cafe_sort-by-relationship_1008-212-166-36.png"
SORT_TITLE = CAFE / "info_cafe_sort-title_636-294-72-40.png"
RELATIONSHIP = CAFE / "btn_cafe_sort-relationship_642-446-308-66.png"
RELATIONSHIP_SELECTED = CAFE / "info_cafe_sort-relationship-selected_642-446-308-66.png"
SORT_CONFIRM = CAFE / "btn_cafe_sort-confirm_640-562-632-60.png"
INVITE_FIRST = CAFE / "btn_cafe_invite-first_1050-302-212-68.png"
# "Notice" alone also matches network-unstable's title; that popup is checked
# (its own message) before this is trusted.
INVITE_NOTICE = CAFE / "info_cafe_invite-notice_884-220-150-56.png"
INVITE_CONFIRM = CAFE / "btn_cafe_invite-confirm_972-706-354-100.png"
INVITE_WAIT = 10  # seconds for "Inviting..." to end; it took ~3 s


def run(delay=1.5, tries=5):
    """Return True once earnings are claimed (or there were none), the
    invitation is used (or on cooldown) and the game is back in the lobby,
    False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = {**game_popups(GAME), "guide": GUIDE}
    # The guide shows right after the load, sometimes after the title does.
    wait_until(lambda: open_popup({"guide": GUIDE}, capture()), GUIDE_WAIT)
    if clear(popups, TITLE, delay, tries) is None:
        log.error(f"{MENU} not usable")
        return False
    if not _earnings(popups, delay, tries):
        return False
    if not _invite(popups, delay, tries):
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _earnings(popups, delay, tries):
    if not tap_until(EARNINGS, EARNINGS_TITLE, delay, tries):
        log.error("earnings dialog not opened")
        return False
    for taps in range(tries + 1):
        screen = past_black()
        popup = open_popup(popups, screen)
        if popup:
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, popups[popup], delay, tries):
                log.error(f"popup_{popup} not closed")
                return False
            continue
        if not locate(EARNINGS_TITLE, screen):
            log.error("earnings dialog closed unexpectedly")
            return False
        if not _yellow(screen):
            log.info("earnings: claimed" if taps else "earnings: nothing to claim")
            break
        if taps == tries:
            log.error(f"earnings: claim still yellow after {tries} taps")
            return False
        match = locate(CLAIM, screen)
        if not match:
            log.error("earnings: claim button not found")
            return False
        if not taps:
            log.info("earnings: claiming")
        x, y = tap(*match[:2])
        log.debug(f"earnings: tap {taps + 1}/{tries} at ({x}, {y})")
        # The reward popup closes on the next loop round (it's a common popup).
        wait_until(lambda: open_popup(popups, capture()), CLAIM_WAIT)
    if not close_popup("earnings", dialog(EARNINGS_TITLE, EARNINGS_CLOSE), delay, tries):
        log.error("earnings dialog not closed")
        return False
    return True


def _invite(popups, delay, tries):
    screen = clear(popups, TITLE, delay, tries)
    if screen is None:
        log.error(f"{MENU} not usable")
        return False
    if not locate(INVITATION, screen):
        log.info("invite: on cooldown, skipping")
        return True
    if not tap_until(INVITATION, INVITATION_TIP, delay, tries):
        log.error("invite list not opened")
        return False
    if locate(SORTED, capture()):
        log.debug("invite: already sorted by relationship rank")
    else:
        log.info("invite: sorting by relationship rank")
        if not (tap_until(SORT, SORT_TITLE, delay, tries)
                and tap_until(RELATIONSHIP, RELATIONSHIP_SELECTED, delay, tries)
                and tap_until(SORT_CONFIRM, SORTED, delay, tries)):
            log.error("invite list not sorted")
            return False
    if not tap_until(INVITE_FIRST, INVITE_NOTICE, delay, tries):
        log.error("invite notice not shown")
        return False
    log.info("invite: inviting first student")
    # Done once the ticket stops matching: it goes grey after the invite.
    if not tap_until(INVITE_CONFIRM, TITLE, delay, tries) or not wait_until(
            lambda: not locate(INVITATION, capture()), INVITE_WAIT):
        log.error("invite not confirmed")
        return False
    log.info("invite: done")
    return True


def _yellow(screen):
    return tint(screen, CLAIM_AREA, "r-b") > YELLOW


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
