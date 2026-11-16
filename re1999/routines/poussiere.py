"""Replay The Poussiere VI at x4 (100 stamina, Dust), then go back to the lobby.

Usage: python -m re1999.routines.poussiere [--debug]

From resource (show > Resource) the routine opens The Poussiere, taps the
stage VI label (which opens the stage panel) and Start, which opens its
battle-prep. Replay mode, the x1-x4 count list and the VICTORY screen work
as in Pneuma Analysis (pneuma_analysis): x4 makes the green button
"-100 Lv.4 Replay", one recorded fight with x4 rewards.

The Poussiere has no daily chances: x4 is 4 x 25 stamina, so the run
spends 100 stamina every time it is called.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import goto, locate, tap_until
from re1999.config import GAME, TEMPLATES_DIR
from re1999.routines import fight_boss

log = logger(__file__)

RESOURCE = TEMPLATES_DIR / "start-screen" / "lobby" / "show" / "resource"
POUSSIERE = RESOURCE / "the-poussiere"
PREP = POUSSIERE / "battle-prep-poussiere"
# Anywhere: The Poussiere is first in resource's row once Pneuma Analysis's
# chances are spent, second while they're left.
OPEN = RESOURCE / "btn_resource_the-poussiere_160-290-560-440_anywhere.png"
STAGE = POUSSIERE / "btn_the-poussiere_stage-vi_560-870-335-55_anywhere.png"
START = POUSSIERE / "btn_the-poussiere_battle-prep-poussiere_1728-892-110-52.png"
REPLAY_MODE = PREP / "btn_battle-prep-poussiere_replay_910-945-66-78.png"
COUNT = PREP / "btn_battle-prep-poussiere_replay-count_1205-950-125-70.png"
X4 = PREP / "btn_battle-prep-poussiere_replay-x4_1245-600-45-45.png"
X4_SET = PREP / "info_battle-prep-poussiere_replay-x4-set_1225-960-60-50.png"
# "Lv.1 Replay" scores 0.92 on this too, so X4_SET is checked before tapping.
REPLAY = PREP / "btn_battle-prep-poussiere_battle_1555-955-240-55.png"
REPLAY_WAIT = 15  # seconds after the one Replay tap for the fight to show


def run():
    """Return True once the x4 replay is won and the lobby is up."""
    if not goto(GAME, "resource"):
        log.error("resource not reached")
        return False
    if not tap_until(OPEN, STAGE, delay=3):
        log.error("the-poussiere not reached")
        return fight_boss.home(False)
    if not tap_until(STAGE, START):
        log.error("The Poussiere VI stage panel not opened")
        return fight_boss.home(False)
    if not tap_until(START, fight_boss.GOALS, delay=3):
        log.error("battle-prep not reached")
        return fight_boss.home(False)
    screen = capture()
    if locate(fight_boss.REPLAY_TEXT, screen):
        log.debug("battle-prep already in replay mode")
    elif not locate(REPLAY_MODE, screen):
        log.warning("no replay icon on battle-prep, nothing replayed")
        return fight_boss.home(False)
    elif not tap_until(REPLAY_MODE, fight_boss.REPLAY_TEXT):
        log.error("battle-prep not in replay mode")
        return fight_boss.home(False)
    if not locate(X4_SET, capture()):
        if not tap_until(COUNT, X4) or not tap_until(X4, X4_SET):
            log.error("replay count not set to x4")
            return fight_boss.home(False)
    # One tap only: what Replay opens without 100 stamina is untested and may
    # offer to buy stamina, which a second tap must not answer.
    if not tap_until(REPLAY, [fight_boss.REPLAYING, fight_boss.VICTORY], delay=REPLAY_WAIT, tries=1):
        log.warning("replay didn't start (stamina under 100?), nothing replayed")
        return fight_boss.home(False)
    if not fight_boss.wait_victory():
        log.error(f"no victory screen within {fight_boss.FIGHT_TIMEOUT} s")
        return False
    log.info("The Poussiere VI replayed at x4")
    if not tap_until(fight_boss.CLOSE_VICTORY, fight_boss.GOALS, delay=8, tries=3):
        log.error("battle-prep not back after the victory screen")
        return False
    return fight_boss.home(True)


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
