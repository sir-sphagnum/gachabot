"""Run Arknights stage 1-12 with Auto Deploy, a given number of times, then go back to the lobby.

Usage: python -m ak.routines.run_stage [RUNS] [--debug]

Does the stage rows of the daily missions, in every tier seen: "Clear any
stage" 1 / 4 / 8 times, "Defeat a total of 1 / 3 enemy leaders in Main Story
stages", "Defeat a total of 100 / 200 / 300 / 400 enemies". 1-12 has W as
its Leader and 30 enemies, so 14 runs (RUNS, default 14) cover all three
rows' top tiers; the reward sets need the 400 tier (ak/notes/dailies.md).
Each run costs 9 Sanity: 126 a day, about half of what refills in one.

1-12 because Auto Deploy needs a 3-star clear made without a support unit
and the leader rows need a Main Story stage with a Leader: 1-12 is both.
2-1 has Auto Deploy but no Leader; 1-11 is a fixed-squad stage with no Auto
Deploy. Auto Deploy replays the recorded clear (common: Finishing a fight
without playing it).

1. Go to the main theme. It opens on the newest stage with its panel open,
   which hides the episode switcher: a tap on empty map closes the panel.
   Tap "EPISODE 01" on the switcher, swipe the map to its right end, where
   1-12 sits, and pick 1-12 (found along the map: it stops a little off
   from swipe to swipe).
2. Turn Auto Deploy on, unless its repeat counter ("x1", shown only while
   it's on) says it already is (common: Settings that stick).
3. Per run: Start once (spends 9 Sanity), then Mission Start once on the
   squad screen (the roster is fixed), then wait for the result with
   core.nav.wait_clear, which closes the account's level-up as it opens
   (common: Level up). A tap on the result goes back to the stage map, with
   1-12 still picked.
4. The lobby routine.

A spend is tapped once and waited on, never retapped (Rule 2's scope). If
Start doesn't reach the squad screen (Sanity ran out: the game offers a
refill, which is never confirmed), the routine stops after the runs it made
and returns True when it made at least one.
"""

import sys

from core.device import wait_until
from core.input import capture, swipe, tap
from core.log import logger, setup
from core.nav import clear, goto, locate, settled, tap_until, wait_clear
from ak.config import GAME, TEMPLATES_DIR
from ak.routines import lobby

log = logger(__file__)

MENU = "main-theme"
THEME = TEMPLATES_DIR / "start-screen" / "lobby" / "terminal" / MENU
EPISODE_01 = THEME / "btn_main-theme_episode-01_1426-938-94-118.png"  # switcher's left, on Episode 02
ON_EPISODE_01 = THEME / "info_main-theme_episode-01-shown_1540-948-176-104.png"
LABEL = THEME / "btn_main-theme_stage-1-12_924-486-76-50_anywhere.png"
TITLE = THEME / "info_main-theme_stage-1-12-title_1282-176-232-50.png"  # panel, once picked
AUTO_DEPLOY = THEME / "btn_main-theme_auto-deploy_1568-858-298-62.png"
REPEAT = THEME / "info_main-theme_repeat-count_1428-862-136-56.png"  # shows only with Auto Deploy on
START = THEME / "btn_main-theme_start_1558-942-308-90.png"
SQUAD = THEME / "squad"
ROSTER = SQUAD / "info_squad_roster-locked_744-1018-560-40.png"
MISSION_START = SQUAD / "btn_squad_stage-result_1554-550-202-418.png"
RESULT = SQUAD / "stage-result" / "info_stage-result_mission-results_100-392-256-36.png"

EMPTY = (640, 960)  # empty map on both episodes: closes a stage's panel
RIGHT_SWIPES = 6  # from Episode 01's start (1-1) to its right end
FIGHT = 360  # seconds to wait for a run's result; runs took ~1.5 min at 2X
SQUAD_WAIT = 10  # seconds for the squad screen after Start
BACK_TO_MAP = 8  # seconds for the stage map after the result's tap (a load between)


def run(runs=14, delay=1.5, tries=5):
    """Return True once up to `runs` runs of 1-12 are done (at least one) and
    the game is back in the lobby, False if it couldn't finish."""
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = lobby.popups()
    if not _pick_stage(popups, delay, tries):
        return False
    if not locate(REPEAT, capture()):
        if not tap_until(AUTO_DEPLOY, REPEAT, delay, tries, popups=popups):
            log.error("auto deploy not turned on")
            return False
        log.info("auto deploy on")
    done = 0
    for n in range(1, runs + 1):
        result = _run_once(n, runs, popups, delay, tries)
        if result is None:  # no Sanity left
            break
        if not result:
            return False
        done += 1
    if not done:
        log.error("no run made")
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _pick_stage(popups, delay, tries):
    """Switch the stage map to Episode 01's right end and pick 1-12."""
    if locate(TITLE, capture()):
        return True
    if not tap_until(EMPTY, [EPISODE_01, ON_EPISODE_01], delay, tries, popups=popups):
        log.error("episode switcher not shown")
        return False
    if not tap_until(EPISODE_01, ON_EPISODE_01, delay, tries, popups=popups):
        log.error("episode 01 not shown")
        return False
    for _ in range(RIGHT_SWIPES):
        swipe(1700, 300, 300, 300)
    settled(5)
    if clear(popups, LABEL, delay, tries) is None:
        log.error("1-12 not on the stage map")
        return False
    if not tap_until(LABEL, TITLE, delay, tries, popups=popups):
        log.error("1-12 not picked")
        return False
    log.info("1-12 picked")
    return True


def _run_once(n, runs, popups, delay, tries):
    """True once a run's result is closed, None when Start was refused (no
    Sanity), False on anything else."""
    screen = clear(popups, TITLE, delay, tries)
    if screen is None or not locate(REPEAT, screen):
        log.error(f"run {n}/{runs}: 1-12 with auto deploy not on screen")
        return False
    x, y = tap(*locate(START, screen)[:2])
    log.debug(f"run {n}/{runs}: start at ({x}, {y})")
    if not wait_until(lambda: locate(ROSTER, capture()), SQUAD_WAIT):
        log.warning(f"run {n}/{runs}: squad screen not reached, out of sanity, stopping")
        return None
    x, y = tap(*locate(MISSION_START, capture())[:2])
    log.debug(f"run {n}/{runs}: mission start at ({x}, {y})")
    if not wait_clear(RESULT, FIGHT, popups=popups):
        log.error(f"run {n}/{runs}: no result after {FIGHT}s")
        return False
    log.info(f"run {n}/{runs}: complete")
    if not tap_until(RESULT, TITLE, BACK_TO_MAP, tries, popups=popups):
        log.error(f"run {n}/{runs}: stage map not back after the result")
        return False
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--debug"]
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run(int(args[0]) if args else 14) else 1)
