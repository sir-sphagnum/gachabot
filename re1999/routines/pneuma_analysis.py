"""Replay Pneuma Analysis VII at x4 with the day's In-depth Analysis Chances, then go back to the lobby.

Usage: python -m re1999.routines.pneuma_analysis [--debug]

From resource (show > Resource) the routine opens Pneuma Analysis, taps the
stage VII label (which opens the stage panel) and Start, which opens
battle-prep. The play icon left of Team 1 switches it to replay mode; the
count box next to "Recorded Rounds" opens a x1-x4 list, and x4 makes the
green button "Lv.4 Replay": one recorded fight with x4 rewards, for both
chances plus 50 stamina. The VICTORY screen and the way back are
In Our Time's (fight_boss).

Pneuma Analysis is first in resource's row while it has chances, with
"In-depth Analysis Chances: n" under it; once they're spent it moves to the
end of the row. So no label at its spot means today's run is done: the
routine goes back to the lobby and returns True without replaying. Without
chances x4 costs 100 stamina, so it never replays then.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import goto, locate, tap_until
from re1999.config import GAME, TEMPLATES_DIR
from re1999.routines import fight_boss

log = logger(__file__)

RESOURCE = TEMPLATES_DIR / "start-screen" / "lobby" / "show" / "resource"
PNEUMA = RESOURCE / "pneuma-analysis"
PREP = PNEUMA / "battle-prep-pneuma"
CHANCES = RESOURCE / "info_resource_analysis-chances_290-795-350-45.png"
OPEN = RESOURCE / "btn_resource_pneuma-analysis_160-290-560-440.png"
SHOP = PNEUMA / "info_pneuma-analysis_psychube-shop_1700-30-190-80.png"
STAGE = PNEUMA / "btn_pneuma-analysis_stage-vii_560-872-400-55_anywhere.png"
START = PNEUMA / "btn_pneuma-analysis_battle-prep-pneuma_1560-890-110-52.png"
REPLAY_MODE = PREP / "btn_battle-prep-pneuma_replay_940-945-66-78.png"
COUNT = PREP / "btn_battle-prep-pneuma_replay-count_1205-950-125-70.png"
X4 = PREP / "btn_battle-prep-pneuma_replay-x4_1245-600-45-45.png"
X4_SET = PREP / "info_battle-prep-pneuma_replay-x4-set_1225-960-60-50.png"
# "Lv.1 Replay" scores 0.92 on this too, so X4_SET is checked before tapping.
REPLAY = PREP / "btn_battle-prep-pneuma_battle_1555-955-240-55.png"


def run():
    """Return True once the x4 replay is won (or the chances are already spent) and the lobby is up."""
    if not goto(GAME, "resource"):
        log.error("resource not reached")
        return False
    if not locate(CHANCES, capture()):
        log.info("no In-depth Analysis Chances left, nothing to replay")
        return fight_boss.home(True)
    if not tap_until(OPEN, SHOP, delay=3):
        log.error("pneuma-analysis not reached")
        return fight_boss.home(False)
    if not tap_until(STAGE, START):
        log.error("Pneuma Analysis VII stage panel not opened")
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
    # Few tries and a long delay: every Replay tap that lands spends the
    # chances and stamina, and the fight takes a few seconds to load.
    if not tap_until(REPLAY, [fight_boss.REPLAYING, fight_boss.VICTORY], delay=8, tries=2):
        log.warning("replay didn't start (stamina under 50?), nothing replayed")
        return fight_boss.home(False)
    if not fight_boss.wait_victory():
        log.error(f"no victory screen within {fight_boss.FIGHT_TIMEOUT} s")
        return False
    log.info("Pneuma Analysis VII replayed at x4")
    if not tap_until(fight_boss.CLOSE_VICTORY, fight_boss.GOALS, delay=8, tries=3):
        log.error("battle-prep not back after the victory screen")
        return False
    return fight_boss.home(True)


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
