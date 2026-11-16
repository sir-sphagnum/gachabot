"""Fight the guild's World Boss until its attempts run out. Entering the guild
on the way there is also the day's guild check-in.

Usage: python -m e7.routines.world_boss [--debug]

1. Go to world-boss (core.nav.goto: lobby > main-menu > guild > world-boss).
   Passing through the guild hall counts as the check-in.
2. Close the World Boss Supporters Reward dialog if it is open (it shows on
   entry when guild members used your supporters), and any common popup.
3. Until Select Team's counter reads 0/2 or the button is grey:
   - tap Select Team until Select Supporters shows (the first supporter is
     preselected), then Team Formation until the team screen shows;
   - tap Auto Assign until all three Team CPs are non-zero (the bonus % is
     no indicator: it can be non-zero before);
   - tap Start once (it spends 20 stamina and one attempt) and wait for Skip;
   - tap Skip until the results or the Battle Rank Reward show;
   - wait for the Battle Rank Reward's Open All, tap it until Confirm shows,
     tap that Confirm until the results are bare, then the results' Confirm
     until world-boss is back.
4. Go back to the lobby (the lobby routine).

Start is never retapped: a tap that landed spends an attempt. If Skip doesn't
show after it (not enough stamina is the likely cause; that screen hasn't been
seen), the routine stops.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import clear, dialog, game_popups, goto, locate, tap_until
from core.vision import diff, load, tint
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "world-boss"
BOSS = TEMPLATES_DIR / "start-screen" / "lobby" / "main-menu" / "guild" / MENU
SUPPORTERS = BOSS / "world-boss-supporters"
TEAM = SUPPORTERS / "world-boss-team"
BATTLE = TEAM / "world-boss-battle"
RESULTS = BATTLE / "world-boss-results"

WEEKLY = BOSS / "info_world-boss_weekly-contribution_1578-124-318-40.png"   # identifies world-boss
SELECT_TEAM = BOSS / "btn_world-boss_world-boss-supporters_1688-978-182-46.png"
# The counter on Select Team. 0/2 scores 1.00 on 0/2 and up to 0.81 on 1/2
# and 2/2, too close to the usual 0.85 (common: Reading a zero).
ATTEMPTS_0 = BOSS / "info_world-boss_attempts-0_1562-976-104-48.png"
ZERO_MIN = 0.95
SUPPORTERS_REWARD = dialog(BOSS / "info_world-boss_supporters-reward-title_626-226-668-62.png",
                           BOSS / "btn_world-boss_supporters-reward-close_860-740-200-90.png")
SUPPORTERS_TITLE = SUPPORTERS / "info_world-boss-supporters_title_38-126-402-62.png"
TEAM_FORMATION = SUPPORTERS / "btn_world-boss-supporters_world-boss-team_1514-966-236-44.png"
TEAM_1 = TEAM / "info_world-boss-team_team-1_50-338-114-46.png"            # identifies the team screen
AUTO_ASSIGN = TEAM / "btn_world-boss-team_auto-assign_158-962-176-44.png"
START = TEAM / "btn_world-boss-team_world-boss-battle_1338-964-76-44.png"
SKIP = BATTLE / "btn_world-boss-battle_world-boss-results_1590-28-100-46.png"
RESULTS_TITLE = RESULTS / "info_world-boss-results_title_1550-36-186-44.png"
RANK_TITLE = RESULTS / "info_world-boss-results_rank-reward-title_758-120-406-62.png"
OPEN_ALL = RESULTS / "btn_world-boss-results_open-all_896-920-128-44.png"
# Open All turns into this Confirm in the same spot once the chests are open.
RANK_CONFIRM = RESULTS / "btn_world-boss-results_rank-reward-confirm_898-920-124-44.png"
CONFIRM = RESULTS / "btn_world-boss-results_confirm_1674-968-114-44.png"

# Select Team greys out at 0/2, and matching can't tell (0.98 grey): green
# minus blue over the button is +26.6..+26.9 lit, +9.4 grey, +4.8 under the
# Supporters Reward dialog (closed before this is read).
SELECT_BOX = (1560, 960, 330, 70)
LIT_MIN = 18
# Team CP numbers, compared with the empty team screen (its screen.png): 0.0
# on every empty capture, 64..75 once Auto Assign filled the team.
CP_BOXES = [(50, 688, 240, 66), (524, 688, 240, 66), (998, 688, 240, 66)]
CP_CHANGED = 20

SKIP_WAIT = 40       # seconds from Start to Skip (~7 s seen: load and intro)
SKIP_DELAY = 4       # the first Skip tap, right as it showed, was once ignored
RANK_WAIT = 30       # seconds from the results to the Battle Rank Reward (counts up first)
MAX_FIGHTS = 5       # safety stop; there are 2 attempts per reset


def run(delay=1.5, tries=5):
    """Return True once the attempts are spent and the game is back in the
    lobby; False if it couldn't go on."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = {**game_popups(GAME), "supporters-reward": SUPPORTERS_REWARD}
    empty = load(TEAM / "screen.png")
    for fight in range(1, MAX_FIGHTS + 1):
        screen = clear(popups, WEEKLY, delay, tries)
        if screen is None:
            log.error(f"{MENU} not usable")
            return False
        if locate(ATTEMPTS_0, screen, ZERO_MIN) or tint(screen, SELECT_BOX, "g-b") < LIT_MIN:
            log.info("attempts 0/2, done")
            break
        log.info(f"fight {fight}")
        if not _fight(empty, popups, delay, tries):
            return False
    else:
        log.error(f"attempts still left after {MAX_FIGHTS} fights")
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _fight(empty, popups, delay, tries):
    if not tap_until(SELECT_TEAM, SUPPORTERS_TITLE, delay, tries, popups=popups):
        log.error("Select Supporters not shown")
        return False
    if not tap_until(TEAM_FORMATION, TEAM_1, delay, tries):
        log.error("team screen not shown")
        return False
    if not tap_until(AUTO_ASSIGN, lambda s: _filled(s, empty), delay, tries):
        log.error("teams not filled")
        return False
    match = locate(START, capture())
    if not match:
        log.error("Start not on screen")
        return False
    tap(*match[:2])
    if wait_until(lambda: locate(SKIP, capture()), SKIP_WAIT) is None:
        log.error(f"no Skip {SKIP_WAIT}s after Start")
        return False
    if not tap_until(SKIP, [RESULTS_TITLE, RANK_TITLE], SKIP_DELAY, tries, popups=False):
        log.error("battle not skipped")
        return False
    if wait_until(lambda: locate(OPEN_ALL, capture()), RANK_WAIT) is None:
        log.error(f"no Open All {RANK_WAIT}s after the results")
        return False
    if not tap_until(OPEN_ALL, RANK_CONFIRM, delay, tries, popups=False):
        log.error("rank reward chests not opened")
        return False
    if not tap_until(RANK_CONFIRM, RESULTS_TITLE, delay, tries, popups=False):
        log.error("Battle Rank Reward not closed")
        return False
    if not tap_until(CONFIRM, WEEKLY, delay, tries):
        log.error(f"{MENU} not back after the results")
        return False
    log.info("fight done")
    return True


def _filled(screen, empty):
    return all(diff(screen, empty, box) > CP_CHANGED for box in CP_BOXES)


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
