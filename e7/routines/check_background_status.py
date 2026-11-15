"""Check Background Battling from the lobby's HUD clock, and claim a finished battle.

Usage: python -m e7.routines.check_background_status [--debug]

1. Get to the active lobby (the lobby routine) and read the HUD clock from
   two frames SPIN_GAP apart, both with the HUD up:
   - spinning (the frames differ): a battle is running. Done.
   - badge lit (the clock's template matches and its orange badge is lit):
     a battle has finished. Claim it.
   - neither, and no clock: nothing running or waiting. Done.
   - a still clock with no badge: not seen yet, so a failure.
2. Claim: tap the clock until auto ("Background Battling") opens, tap
   Calculate until Calculation Complete or the claimed Close shows, close
   Calculation Complete with "Tap to close", then tap Close until the lobby's
   main-menu icon shows.
3. Read the clock again. The claim counts once the clock is gone, whatever
   the steps in 2 reported.

status() does steps 1-3 and returns the state, for routines that need it
(hunt starts nothing while a battle runs).
"""

import sys
import time
from pathlib import Path

import numpy as np

from core.input import capture
from core.log import logger, setup
from core.nav import game_popups, locate, open_popup, past_black, tap_until
from core.vision import save
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

COMMON = TEMPLATES_DIR / "common"
AUTO = COMMON / "auto"
CLOCK = COMMON / "hud" / "btn_hud_auto_1388-12-72-68.png"
TITLE = AUTO / "info_auto_title_778-76-366-58.png"                    # "Background Battling"
CALCULATE = AUTO / "btn_auto_calculate_780-908-370-70.png"
COMPLETE_TITLE = AUTO / "info_auto_complete-title_726-156-468-64.png"  # "Calculation Complete"
COMPLETE_CLOSE = AUTO / "btn_auto_complete-close_860-835-200-95.png"   # "Tap to close"
CLOSE = AUTO / "btn_auto_close_780-908-370-70.png"

# A spinning clock changes 38-49 (mean pixel difference) between frames
# 0.3 s apart; still icons change 0.0-0.1. The still clock's template matched
# a spinning clock on 1 frame in 6, so spinning is decided from this first.
CLOCK_BOX = (1388, 12, 72, 68)
SPIN_MIN = 15
SPIN_GAP = 0.3
# The clock's template scores the same with the badge lit or not, so lit is
# told by colour: mean red minus blue over the badge is +207 lit. arena-team,
# with no clock, reads +147 there, so the clock's template must match too.
BADGE_BOX = (1392, 17, 14, 14)
BADGE_MIN = 180

NONE, RUNNING, CLAIMED = "none", "running", "claimed"


def run():
    """True once the clock shows nothing to do: no clock, a battle running, or
    a finished battle now claimed. False if the HUD wasn't seen or the claim
    didn't go through."""
    return status() is not None


def status(delay=1.5, tries=5):
    """NONE (no battle running or waiting), RUNNING (a battle running) or
    CLAIMED (a finished battle, now claimed), with the game in the lobby.
    None on failure.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    popups = game_popups(GAME)
    clock = _read(popups)
    if clock in (None, RUNNING, NONE):
        return clock
    _claim(popups, delay, tries)
    after = _read(popups)
    if after == NONE:
        log.info("claimed, back in lobby")
        return CLAIMED
    if after is not None:
        log.error(f"clock still {after} after claiming")
    return None


def _read(popups, attempts=3):
    """The clock's state: NONE, RUNNING, "finished", or None if the HUD
    wasn't seen or the clock shows neither spin nor badge."""
    for attempt in range(1, attempts + 1):
        if not lobby.run():
            log.error("lobby not reached")
            return None
        first = past_black()
        if open_popup(popups, first):
            continue    # Rule 1: the lobby routine closes it on the next attempt
        time.sleep(SPIN_GAP)
        second = capture()
        if not (locate(lobby.MAIN_MENU, first) and locate(lobby.MAIN_MENU, second)):
            log.debug(f"HUD not showing, attempt {attempt}/{attempts}")
            continue
        change = _changed(first, second, CLOCK_BOX)
        badge = _redness(first, BADGE_BOX)
        log.debug(f"clock change {change:.1f}, badge {badge:+.0f}")
        if change >= SPIN_MIN:
            log.info("clock spinning, a battle is running")
            return RUNNING
        clock = locate(CLOCK, first)
        if clock and badge >= BADGE_MIN:
            log.info("clock badge lit, a battle has finished, claiming")
            return "finished"
        if clock:
            log.error("clock still but its badge isn't lit, state unknown")
            return None
        log.info("no clock, nothing running or waiting")
        return NONE
    log.error(f"HUD not seen in {attempts} attempts")
    return None


def _claim(popups, delay, tries):
    """Tap the clock, Calculate, Tap to close and Close. Logs each step that
    fails; whether the claim went through is read off the clock afterwards."""
    if not tap_until(CLOCK, TITLE, delay, tries, popups=popups):
        log.warning("auto not opened")
        return
    if not locate(CALCULATE, past_black()):
        log.warning("auto shows no Calculate")
        return
    # Calculation Complete's title has gone unseen after a Calculate that did
    # claim the rewards (notes/UI.md, check-background-status), so its "Tap to
    # close" and the claimed Close count as done too.
    done = tap_until(CALCULATE, [COMPLETE_TITLE, COMPLETE_CLOSE, CLOSE], delay, tries, popups=popups)
    if not done:
        Path("logs").mkdir(exist_ok=True)
        path = Path("logs") / f"check_background_status-{time.strftime('%Y%m%d-%H%M%S')}.png"
        save(capture(), path)
        log.warning(f"Calculation Complete not shown, screen saved to {path.as_posix()}")
        return
    if done[0] != str(CLOSE) and not tap_until(COMPLETE_CLOSE, CLOSE, delay, tries, popups=popups):
        log.warning("Calculation Complete not closed")
        return
    if not tap_until(CLOSE, lobby.MAIN_MENU, delay, tries, popups=popups):
        log.warning("auto not closed")


def _cut(screen, box):
    x, y, w, h = box
    return screen[y:y + h, x:x + w].astype(np.int16)


def _changed(a, b, box):
    return float(np.abs(_cut(a, box) - _cut(b, box)).mean())


def _redness(screen, box):
    """Mean red minus blue over `box` (BGR)."""
    cut = _cut(screen, box)
    return float((cut[..., 2] - cut[..., 0]).mean())


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:])
    sys.exit(0 if run() else 1)
