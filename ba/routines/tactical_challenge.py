"""Spend every Tactical Challenge ticket on the top opponent, then claim the
Time and Daily Rewards.

Usage: python -m ba.routines.tactical_challenge [--debug]

1. Go to tactical-challenge (core.nav.goto: lobby > Campaign > Tactical
   Challenge).
2. Until the ticket count reads 0: tap the top opponent row (Battle
   Opponent opens), Attack Formation, Mobilize, then >> top right of the
   battle to skip it. A win shows Battle Complete > Confirm > REWARD
   ACQUIRED > Confirm, a loss LOSE > Confirm > Tip > Confirm; both end back
   on tactical-challenge, sometimes under "Best Season Record Reached!"
   (closed with Confirm). The top row is fought even when it is much
   stronger: a loss only costs the ticket.
3. Claim Time Reward, then Daily Reward, each only while its Claim is
   yellow; each opens the common reward popup.
4. Home, then the lobby routine.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import (close_popup, dialog, game_popups, goto, locate, open_popup,
                      past_black, tap_until)
from core.vision import load
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby

log = logger(__file__)

MENU = "tactical-challenge"
TC = TEMPLATES_DIR / "start-screen" / "lobby" / "campaign" / MENU
AF = TC / "attack-formation"
TITLE = TC / "info_tactical-challenge_title_158-12-372-50.png"
HOME = TC / "btn_tactical-challenge_lobby_1830-12-54-46.png"

# First digit of "Tickets Owned N/5": 1.00 on 0, at most 0.73 on 5-1
# (common: Reading a zero).
ZERO = TC / "info_tactical-challenge_tickets-zero_326-716-20-36.png"
ZERO_MATCH = 0.90
FIGHTS = 6  # one more than a full stock of tickets, in case a count misreads

# The top row is tapped as a point: its crop holds the opponent's portrait,
# rank and team, which change with every list.
TOP_ROW = (1268, 375)
OPPONENT_TITLE = TC / "info_tactical-challenge_battle-opponent-title_776-118-372-56.png"
ATTACK = TC / "btn_tactical-challenge_attack-formation_800-812-326-88.png"
AF_TITLE = AF / "info_attack-formation_title_158-12-400-50.png"
MOBILIZE = AF / "btn_attack-formation_mobilize_1640-976-220-62.png"
# >> top right of the battle HUD. It slides in over the first second or two,
# so it is located on the live screen before each tap.
SKIP = AF / "btn_attack-formation_battle-skip_1812-34-80-70.png"
LOAD_DELAY = 4      # seconds per round for the battle to load (6-9 s seen)
BATTLE_DELAY = 5    # seconds per round for the result after >>
BATTLE_TRIES = 12   # rounds; an unskipped battle lasts up to 3:00
WIN_CONFIRM = AF / "btn_attack-formation_battle-confirm_1656-952-196-88.png"
LOSE = AF / "info_attack-formation_battle-lose_726-424-468-160.png"
LOSE_CONFIRM = AF / "btn_attack-formation_lose-confirm_788-936-348-104.png"
TIP = AF / "info_attack-formation_lose-tip_444-132-156-76.png"
# The yellow Confirm at the bottom centre of both the win's reward screen
# and the loss's tip (0.94-1.00 on each). The win's "REWARD ACQUIRED!" also
# scores 0.96 as the common reward popup, so these steps don't check popups:
# that popup's close spot is this same Confirm.
BOTTOM_CONFIRM = AF / "btn_attack-formation_reward-confirm_800-940-324-96.png"

BEST_RECORD = dialog(TC / "info_tactical-challenge_best-record-title_634-208-652-56.png",
                     TC / "btn_tactical-challenge_best-record-confirm_800-764-328-96.png")
BEST_WAIT = 2  # seconds to watch for it after the result closes

# (name, Claim's centre, its box as (rows, cols)). Mean red minus blue over
# the box: +167 yellow, -2 grey. The templates score 0.81 on grey, so colour
# decides.
CLAIMS = [("time reward", (529, 582), (slice(548, 616), slice(452, 606))),
          ("daily reward", (529, 700), (slice(666, 734), slice(452, 606)))]
YELLOW = 80
CLAIM_WAIT = 5  # seconds for the reward popup to show after Claim


def run(delay=1.5, tries=5):
    """Return True once the tickets are spent, the rewards claimed and the
    game is back in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = {**game_popups(GAME), "best-record": BEST_RECORD}
    if not _fights(popups, delay, tries):
        return False
    for claim in CLAIMS:
        if not _claim(*claim, popups, delay, tries):
            return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _fights(popups, delay, tries):
    for fight in range(1, FIGHTS + 1):
        screen = _clear(popups, delay, tries)
        if screen is None:
            return False
        if locate(ZERO, screen, ZERO_MATCH):
            log.info("no tickets left" if fight > 1 else "no tickets, nothing to fight")
            return True
        log.info(f"fight {fight}")
        if not _fight(delay, tries):
            return False
        # The best-record dialog shows right after the result closes, over a
        # title that already matches.
        wait_until(lambda: open_popup({"best-record": BEST_RECORD}, capture()), BEST_WAIT)
    log.error(f"tickets left after {FIGHTS} fights")
    return False


def _fight(delay, tries):
    """One fight on the top row, from tactical-challenge back to it."""
    if not tap_until(TOP_ROW, OPPONENT_TITLE, delay, tries):
        log.error("battle opponent not opened")
        return False
    if not tap_until(ATTACK, AF_TITLE, delay, tries):
        log.error("attack formation not reached")
        return False
    if not tap_until(MOBILIZE, SKIP, LOAD_DELAY, tries, popups=False):
        log.error("battle not started")
        return False
    hit = tap_until(SKIP, [WIN_CONFIRM, LOSE], BATTLE_DELAY, BATTLE_TRIES, popups=False)
    if not hit:
        log.error("battle result not shown")
        return False
    if hit[0] == WIN_CONFIRM:
        log.info("won")
        steps = [(WIN_CONFIRM, BOTTOM_CONFIRM, "reward")]
    else:
        log.info("lost")
        steps = [(LOSE_CONFIRM, TIP, "tip")]
    steps.append((BOTTOM_CONFIRM, TITLE, MENU))
    for button, expected, name in steps:
        if not tap_until(button, expected, delay, tries, popups=False):
            log.error(f"{name} not reached")
            return False
    return True


def _claim(name, point, box, popups, delay, tries):
    """Tap Claim while it is yellow, closing the reward popup it opens."""
    for taps in range(tries + 1):
        screen = _clear(popups, delay, tries)
        if screen is None:
            return False
        b, _, r = load(screen)[box].reshape(-1, 3).mean(axis=0)
        if r - b <= YELLOW:
            log.info(f"{name}: claimed" if taps else f"{name}: nothing to claim")
            return True
        if taps == tries:
            log.error(f"{name}: claim still yellow after {tries} taps")
            return False
        if not taps:
            log.info(f"{name}: claiming")
        tap(*point)
        # The reward popup closes on the next round (_clear).
        wait_until(lambda: open_popup(popups, capture()), CLAIM_WAIT)
    return False


def _clear(popups, delay, tries):
    """The current screen once no popup or dialog is open and the title
    shows, or None (logged) if that can't be had."""
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


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
