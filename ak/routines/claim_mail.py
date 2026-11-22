"""Collect every Arknights mail attachment with Collect All, then go back to the lobby.

Usage: python -m ak.routines.claim_mail [--debug]

Collect All is blue whether or not anything is left. With attachments it
opens the common resource-gained popup; without, a "No mail to claim" toast
shows at the top right for a few seconds. Either one means the mail is done.

The tap runs with popups=False: resource-gained is one of the game's common
popups, so tap_until would otherwise close it as an obstruction and keep
tapping Collect All instead of reporting it as the result.
"""

import sys

from core.log import logger, setup
from core.nav import close_popup, game_popups, goto, tap_until
from ak.config import GAME, TEMPLATES_DIR
from ak.routines import lobby

log = logger(__file__)

MAIL = TEMPLATES_DIR / "start-screen" / "lobby" / "mail"
COLLECT_ALL = MAIL / "btn_mail_collect-all_1546-952-330-92.png"
NO_MAIL = MAIL / "info_mail_no-mail-toast_1572-160-190-38.png"
GAINED = (TEMPLATES_DIR / "common" / "popups" / "resource-gained"
          / "info_resource-gained_title_840-214-240-48.png")


def run():
    """Return True once the mail is collected (or had nothing to collect) and the lobby is up."""
    if not goto(GAME, "mail"):
        log.error("mail not reached")
        return False
    hit = tap_until(COLLECT_ALL, [GAINED, NO_MAIL], popups=False)
    if not hit:
        log.error("collect all showed neither rewards nor the no-mail toast")
        return False
    if hit[0] == str(NO_MAIL):
        log.info("nothing to collect")
    else:
        log.info("collected, closing rewards")
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
