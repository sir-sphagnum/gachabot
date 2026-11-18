"""Receive every E7 mail Receive All can take, then go back to the lobby.

Usage: python -m e7.routines.claim_mail [--debug]

1. Go to mail (the HUD's envelope on the active lobby).
2. Tap Receive All until its question ("Would you like to receive all mail
   in your inbox?") shows. It shows even when nothing can be received.
3. Confirm, until "Received Reward" or the "Receive All cannot be used with
   this mail." toast shows. The toast means nothing Receive All can take was
   left: done. Otherwise Tap to close.
4. The lobby routine.

Receive All leaves GM mail in the mailbox: each one unlocks only after its
"Move to Link" opens an outside link, which the bot never taps. Heroes and
equipment stay too while the inventory is full. So mail left over after the
claim is expected, not a failure.

Confirm and Tap to close are shared with other dialogs (the quit dialog,
every "Received Reward"), so each is tapped only right after the step that
opens its dialog (common: Shared buttons). The question isn't passed to
tap_until as a popup: its close button is Confirm, so closing it would claim.
"""

import sys

from core.log import logger, setup
from core.nav import close_popup, dialog, goto, tap_until
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "mail"
MAIL = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
RECEIVE_ALL = MAIL / "btn_mail_receive-all_1600-972-230-62.png"
QUESTION = MAIL / "info_mail_receive-all-question_650-365-620-48.png"
CONFIRM = MAIL / "btn_mail_receive-all-confirm_976-665-293-86.png"
RECEIVED_TITLE = MAIL / "info_mail_received-title_778-225-364-60.png"  # "Received Reward"
RECEIVED = dialog(RECEIVED_TITLE, MAIL / "btn_mail_received-close_870-770-180-50.png")  # "Tap to close"
NOTHING = MAIL / "info_mail_cannot-toast_705-975-510-42.png"  # "Receive All cannot be used with this mail."


def run(delay=1.5, tries=5):
    """Return True once Receive All has taken what it can (or had nothing to
    take) and the game is back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not _receive_all(delay, tries):
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _receive_all(delay, tries):
    hit = tap_until(RECEIVE_ALL, [QUESTION, NOTHING], delay, tries)
    if not hit:
        log.error("receive all showed neither its question nor the cannot-be-used toast")
        return False
    if hit[0] == str(NOTHING):
        log.info("nothing Receive All can take (GM mail may be left)")
        return True
    log.info("confirming")
    hit = tap_until(CONFIRM, [RECEIVED_TITLE, NOTHING], delay, tries, popups=False)
    if not hit:
        log.error("confirm showed neither Received Reward nor the toast")
        return False
    if hit[0] == str(NOTHING):
        log.info("nothing Receive All can take (GM mail may be left)")
        return True
    if not close_popup("received", RECEIVED, delay, tries):
        log.error("Received Reward not closed")
        return False
    log.info("received")
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
