"""Claim the daily tasks' rewards (common: Daily missions).

Usage: python -m ba.routines.claim_dailies [--debug]

1. Go to Tasks (core.nav.goto); it opens on the All tab.
2. While Claim All is yellow, tap it. It opens the reward popup, sometimes
   after the mailbox popup (ownership limit reached); both are common
   popups and close on the next round. A claim can unlock "Complete at least
   5 Daily Task(s)", which lights Claim All again, so it's tapped until grey.
3. Claim All never takes the "Complete at least 8 Daily Task(s)" milestone
   on the bottom bar: tap its Claim while yellow. It pays at once, with no
   popup, and turns grey ("Complete"). When Claim All completed the 8th task,
   the Claim lights a moment after the reward popup closes, so the routine
   waits up to MILESTONE_WAIT for it before taking it as grey (Rule 2).
4. Back to the lobby: Home icon, then the lobby routine.

Grey means claimed or not earned yet, which counts as done (Rule 6).
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

MENU = "tasks"
TASKS = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
TITLE = TASKS / "info_tasks_title_158-14-116-48.png"
HOME = TASKS / "btn_tasks_lobby_1830-12-54-46.png"

# Both buttons are tapped as points and read lit or grey by colour: the grey
# Claim All still scores 0.84 on its template. Mean red minus blue over each
# box is +164 to +168 yellow, -2 to -8 grey (recon of 2026-11-17).
CLAIM_ALL = (1570, 962, 312, 88)
MILESTONE = (1388, 962, 146, 84)
YELLOW = 80
CLAIM_WAIT = 5  # seconds for a claim's popup to show, or its button to go grey
MILESTONE_WAIT = 5  # seconds for the milestone's Claim to light after Claim All


def run(delay=1.5, tries=5):
    """Return True once nothing on Tasks is left yellow and the game is back
    in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = game_popups(GAME)
    if not _claim("claim all", CLAIM_ALL, popups, delay, tries):
        return False
    wait_until(lambda: _yellow(capture(), MILESTONE), MILESTONE_WAIT)
    if not _claim("milestone", MILESTONE, popups, delay, tries):
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _claim(name, box, popups, delay, tries):
    """Tap the button in `box` while it's yellow, closing what each tap opens."""
    for taps in range(tries + 1):
        screen = clear(popups, TITLE, delay, tries)
        if screen is None:
            log.error(f"{MENU} not usable")
            return False
        if not _yellow(screen, box):
            log.info(f"{name}: claimed" if taps else f"{name}: nothing to claim")
            return True
        if taps == tries:
            log.error(f"{name}: still yellow after {tries} taps")
            return False
        if not taps:
            log.info(f"{name}: claiming")
        x, y = tap(box[0] + box[2] // 2, box[1] + box[3] // 2)
        log.debug(f"{name}: tap {taps + 1}/{tries} at ({x}, {y})")
        # The popups close on the next round, in clear.
        wait_until(lambda: open_popup(popups, s := capture()) or not _yellow(s, box), CLAIM_WAIT)
    return False


def _yellow(screen, box):
    return tint(screen, box, "r-b") > YELLOW


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
