"""Claim every Blue Archive mail with Claim All, then go back to the lobby.

Usage: python -m ba.routines.claim_mail [--debug]

1. Go to the mailbox (lobby's envelope icon, top right).
2. While Claim All is yellow, tap it. It opens the common reward popup,
   closed on the next round by core.nav.clear; an item at its ownership
   limit may also open the mailbox popup. One tap claims at most 100 mails,
   so a fuller mailbox keeps Claim All yellow for another tap.
3. Home, then the lobby routine.

A grey Claim All means nothing to claim, which counts as done.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import clear, game_popups, goto, open_popup, tap_until
from core.vision import tint
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby

log = logger(__file__)

MENU = "mail"
MAIL = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
TITLE = MAIL / "info_mail_title_160-12-160-50.png"
HOME = MAIL / "btn_mail_lobby_1830-12-54-46.png"

# Claim All is tapped as a point and read lit or grey by colour: grey still
# scores 0.89 on its template. Mean red minus blue over the box is +164
# yellow, -1 to -3 grey (recon of 2026-11-18).
CLAIM_ALL = (1550, 965, 305, 80)
YELLOW = 80
CLAIM_WAIT = 5  # seconds for the reward popup to show, or Claim All to go grey


def run(delay=1.5, tries=5):
    """Return True once Claim All is grey and the game is back in the lobby,
    False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not _claim(game_popups(GAME), delay, tries):
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _claim(popups, delay, tries):
    """Tap Claim All while it's yellow, closing what each tap opens."""
    for taps in range(tries + 1):
        screen = clear(popups, TITLE, delay, tries)
        if screen is None:
            log.error(f"{MENU} not usable")
            return False
        if not _yellow(screen):
            log.info("claimed" if taps else "nothing to claim")
            return True
        if taps == tries:
            log.error(f"claim all still yellow after {tries} taps")
            return False
        if not taps:
            log.info("claiming")
        x, y = tap(CLAIM_ALL[0] + CLAIM_ALL[2] // 2, CLAIM_ALL[1] + CLAIM_ALL[3] // 2)
        log.debug(f"claim all: tap {taps + 1}/{tries} at ({x}, {y})")
        # The popups close on the next round, in clear.
        wait_until(lambda: open_popup(popups, s := capture()) or not _yellow(s), CLAIM_WAIT)
    return False


def _yellow(screen):
    return tint(screen, CLAIM_ALL, "r-b") > YELLOW


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
