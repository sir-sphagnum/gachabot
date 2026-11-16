"""Claim every Reverse: 1999 mail attachment with Claim All, then go back to the lobby.

Usage: python -m re1999.routines.claim_mail [--debug]

Claim All shows whether or not there is anything to claim. With attachments
it opens the common obtained popup; without, a "No mail with attachment"
toast shows at the top right. Either one means the mail is done.

The tap runs with popups=False: the obtained popup is one of the game's
common popups, so tap_until would otherwise close it as an obstruction and
keep tapping Claim All instead of reporting it as the result.
"""

import sys

from core.log import logger, setup
from core.nav import close_popup, game_popups, goto, tap_until
from re1999.config import GAME, TEMPLATES_DIR
from re1999.routines import lobby

log = logger(__file__)

MAIL = TEMPLATES_DIR / "start-screen" / "lobby" / "mail"
CLAIM_ALL = MAIL / "btn_mail_claim-all_182-900-242-56.png"
NO_ATTACHMENT = MAIL / "info_mail_no-attachment-toast_1505-150-400-75.png"
OBTAINED = TEMPLATES_DIR / "common" / "popups" / "obtained" / "info_obtained_title_872-178-176-46.png"


def run():
    """Return True once the mail is claimed (or had nothing to claim) and the lobby is up."""
    if not goto(GAME, "mail"):
        log.error("mail not reached")
        return False
    hit = tap_until(CLAIM_ALL, [OBTAINED, NO_ATTACHMENT], popups=False)
    if not hit:
        log.error("claim all showed neither rewards nor the no-attachment toast")
        return False
    if hit[0] == str(NO_ATTACHMENT):
        log.info("nothing to claim")
    else:
        log.info("claimed, closing rewards")
        if not close_popup("obtained", game_popups(GAME)["obtained"]):
            log.error("rewards not closed")
            return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
