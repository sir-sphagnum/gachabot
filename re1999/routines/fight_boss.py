"""Replay In Our Time's stage 16, Heaven Apostles, on Hard once, then go back to the lobby.

Usage: python -m re1999.routines.fight_boss [--debug]

show's Story tab opens either on the volume list or inside "The Living and
the Rest" scrolled to its end, so the routine goes to show, taps the volume
poster while its label shows, and swipes the chapter row back until the In Our Time
poster shows (notes/UI.md, show). From in-our-time the routine taps the Heaven Apostles
label on the stage timeline, which opens the stage panel; Hard, then Start,
opens battle-prep. The play icon left of Team 1 switches battle-prep to
replay mode, whose green "Lv.1 Replay" runs the recorded fight at x1 for 14
stamina. The fight ends on a VICTORY screen that a tap anywhere closes, back
to battle-prep through a loading screen; Home then goes to the lobby.

Replay is only tapped when its button shows, and only until the fight starts:
each tap that lands spends 14 stamina.
"""

import sys
import time

from core.input import capture, swipe, tap
from core.log import logger, setup
from core.nav import goto, locate, tap_until
from re1999.config import GAME, TEMPLATES_DIR
from re1999.routines import lobby

log = logger(__file__)

SHOW = TEMPLATES_DIR / "start-screen" / "lobby" / "show"
VOLUME = SHOW / "btn_show_living-and-rest-volume_148-818-400-58.png"
# The volume's label ignores taps; its poster art above it opens the volume.
VOLUME_POSTER = (345, 450)
POSTER = SHOW / "btn_show_in-our-time_767-316-160-452_anywhere.png"
IN_OUR_TIME = SHOW / "in-our-time"
TRAIL = IN_OUR_TIME / "info_in-our-time_trail-icon_478-40-66-66.png"
ROW_SWIPE = (400, 550, 1500, 550)  # left to right across the chapter row: scrolls it back
ROW_SWIPES = 6  # one swipe brought In Our Time in from the row's end
PREP = IN_OUR_TIME / "battle-prep"
BATTLE = PREP / "battle"
STAGE = IN_OUR_TIME / "btn_in-our-time_heaven-apostles_558-864-336-50_anywhere.png"
HARD = IN_OUR_TIME / "btn_in-our-time_hard_1700-370-95-50.png"
START = IN_OUR_TIME / "btn_in-our-time_battle-prep_1726-890-110-52.png"
GOALS = PREP / "info_battle-prep_goals_98-143-82-38.png"
REPLAY_MODE = PREP / "btn_battle-prep_replay_902-945-66-78.png"
REPLAY_TEXT = PREP / "info_battle-prep_replay-text_798-70-500-34.png"
REPLAY = PREP / "btn_battle-prep_battle_1543-955-240-55.png"
HOME = PREP / "btn_battle-prep_lobby_186-42-56-56.png"
REPLAYING = BATTLE / "info_battle_replaying_1708-205-148-45.png"
VICTORY = BATTLE / "info_battle_victory-title_1150-160-450-95.png"
CLOSE_VICTORY = (1769, 64)  # any spot closes the victory screen; this one was tested
HARD_WAIT = 1.5  # seconds for the panel to switch to Hard
FIGHT_TIMEOUT = 180  # seconds; a replay took ~50
FIGHT_POLL = 3


def _open_in_our_time():
    """Go to show and open In Our Time from whichever Story level shows."""
    if not goto(GAME, "show"):
        return False
    # The poster's spot is a chapter poster inside the volume, so it is retapped
    # only while the volume list (its label) still shows.
    if locate(VOLUME, capture()) and not tap_until(VOLUME_POSTER, [lambda s: not locate(VOLUME, s)], delay=2):
        return False
    for _ in range(ROW_SWIPES):
        if locate(POSTER, capture()):
            return tap_until(POSTER, [TRAIL], delay=2)
        swipe(*ROW_SWIPE, 600)
        time.sleep(1.5)
    return False


def run():
    """Return True once the replay is won and the lobby is up."""
    if not _open_in_our_time():
        log.error("in-our-time not reached")
        return False
    if not tap_until(STAGE, HARD):
        log.error("Heaven Apostles stage panel not opened")
        return home(False)
    hit = locate(HARD, capture())
    if not hit:
        log.error("Hard not on the stage panel")
        return home(False)
    tap(hit[0], hit[1])
    time.sleep(HARD_WAIT)
    if not tap_until(START, GOALS, delay=3):
        log.error("battle-prep not reached")
        return home(False)
    # battle-prep opens in replay mode once a replay has run there, and the
    # play icon only shows outside it.
    screen = capture()
    if locate(REPLAY_TEXT, screen):
        log.debug("battle-prep already in replay mode")
    elif not locate(REPLAY_MODE, screen):
        log.warning("no replay icon on battle-prep, nothing replayed")
        return home(False)
    elif not tap_until(REPLAY_MODE, REPLAY_TEXT):
        log.error("battle-prep not in replay mode")
        return home(False)
    # Few tries and a long delay: every Replay tap that lands spends stamina,
    # and the fight takes a few seconds to load after it.
    if not tap_until(REPLAY, [REPLAYING, VICTORY], delay=8, tries=2):
        log.warning("replay didn't start (stamina under 14?), nothing replayed")
        return home(False)
    if not wait_victory():
        log.error(f"no victory screen within {FIGHT_TIMEOUT} s")
        return False
    log.info("Heaven Apostles (Hard) replayed")
    if not tap_until(CLOSE_VICTORY, GOALS, delay=8, tries=3):
        log.error("battle-prep not back after the victory screen")
        return False
    return home(True)


def wait_victory():
    """Wait for the victory screen. True once it shows."""
    end = time.monotonic() + FIGHT_TIMEOUT
    while time.monotonic() < end:
        if locate(VICTORY, capture()):
            return True
        time.sleep(FIGHT_POLL)
    return False


def home(result):
    """Go to the lobby, then return `result` (False if the lobby isn't reached)."""
    if not tap_until(HOME, lobby.CREW, delay=8):
        log.error("lobby not reached")
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return result


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
