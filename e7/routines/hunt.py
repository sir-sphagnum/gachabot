"""Start Background Battling on a hunt's Hell difficulty, paid with stamina.

Usage: python -m e7.routines.hunt [--hunt NAME] [--leifs N] [--debug]

1. Get to the active lobby. If the HUD clock is spinning, a background battle
   is already running: stop, starting nothing.
2. Go to hunt (core.nav.goto) and pick the hunt NAME (default wyvern) from the
   cards under Available Dungeons. The cards move: tapping one scrolls the list
   so it shows below the one before it. So until NAME is chosen, tap the
   showing card nearest it in the list, or, when that one is already chosen,
   one card step past it (the next card's label is then mostly off screen).
   The chosen hunt is told by its first Exclusive Reward icon.
3. Tap Hunt - Hell until hunt-team shows, then Background Battling until its
   dialog opens.
4. Tick Use Owned Energy First. When it's greyed out, it can't be ticked: go
   on without it.
5. Tap +1 while the leif cost shows 0 and the count still changes. Each step
   is 80 stamina (4 runs) while stamina lasts, then 1 leif. With --leifs 0 (the
   default), a step that costs a leif is taken back with -1. If even the first
   step costs a leif, stamina is too low: close the dialog and stop (success).
   With --leifs N, tap +1 N-1 more times past the first leif step.
6. Tap Start, then the confirm dialog's Confirm, until hunt-team shows again.
7. Go back to the lobby.

Ogre has no Hunt - Hell difficulty, so it's refused.
"""

import argparse
import sys
import time

import numpy as np

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import game_popups, goto, locate, open_popup, past_black, tap_until
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "hunt"
HUNT = TEMPLATES_DIR / "start-screen" / "lobby" / "main-menu" / "battle" / MENU
TEAM = HUNT / "hunt-team"
TITLE = HUNT / "info_hunt_title_54-228-118-56.png"                  # the big "Hunt" heading
HELL = HUNT / "btn_hunt_hunt-team_1170-578-142-42.png"              # "Hunt - Hell"
QUICK_BATTLING = TEAM / "info_hunt-team_quick-battling_1446-682-176-40.png"  # identifies hunt-team, dim under its dialogs
BACKGROUND = TEAM / "btn_hunt-team_background-battling_918-838-130-56.png"
DIALOG_TITLE = TEAM / "info_hunt-team_dialog-title_428-86-326-54.png"
DIALOG_CLOSE = TEAM / "btn_hunt-team_dialog-close_870-1020-180-44.png"  # "Tap to close", also the check-in dialog's
# With a background battle running, Background Battling opens auto's progress
# view (Battle Progress, Stop) instead of the dialog. Closed by a tap on its
# "Tap to close.", well below Stop; DIALOG_CLOSE doesn't match it.
AUTO_TITLE = TEMPLATES_DIR / "common" / "auto" / "info_auto_title_778-76-366-58.png"
RUNNING_CLOSE = (960, 1041)
ENERGY = TEAM /"btn_hunt-team_use-energy-first_835-461-46-46.png"   # the box, unticked
TICKED = TEAM / "info_hunt-team_use-energy-first-ticked_835-461-46-46.png"
PLUS = TEAM / "btn_hunt-team_plus-1_1312-619-76-50.png"
MINUS = TEAM / "btn_hunt-team_minus-1_920-619-78-50.png"
LEIF_ZERO = TEAM / "info_hunt-team_leif-cost-0_1242-752-36-38_white.png"  # 1.00 on "0", 0.49 on "1"
START = TEAM / "btn_hunt-team_start_786-905-343-72.png"
START_QUESTION = TEAM / "info_hunt-team_start-question_670-462-580-50.png"
# The same Confirm as the lobby's quit dialog (1.00 there), so it's tapped
# only once the Start question shows.
START_CONFIRM = TEAM / "btn_hunt-team_start-confirm_975-647-293-86.png"

# Cards under Available Dungeons, in list order.
HUNTS = ["wyvern", "golem", "banshee", "azimanak", "caides", "ogre"]
NO_HELL = {"ogre"}
# Card labels sit 306 px apart. The list shows from below "Available
# Dungeons" to the screen's bottom edge.
CARD_STEP = 306
CARD_Y_MIN = 220
CARD_Y_MAX = 1065

# The count "n/max" above the slider: a +1 or -1 that changes nothing here has
# hit the end of the range.
COUNT_BOX = (1080, 615, 170, 60)
COUNT_CHANGED = 2    # mean pixel difference: 5.9-7.4 on a changed count, 0.0 on the same one
# A spinning HUD clock changes 42-49 (mean pixel difference) between frames
# 0.3 s apart; still icons change 0.0-0.1.
CLOCK_BOX = (1388, 12, 72, 68)
SPIN_MIN = 15
SPIN_GAP = 0.3


def _card(name):
    return next(HUNT.glob(f"btn_hunt_{name}_*_anywhere.png"))


def _reward(name):
    return next(HUNT.glob(f"info_hunt_{name}-reward_*.png"))


def run(hunt="wyvern", leifs=0, delay=1.5, tries=5):
    """Return True once Background Battling started on `hunt` (or stamina was
    too low for a run without leifs) and the game is back in the lobby; False
    if a background battle was already running or a step failed.

    hunt: a name from HUNTS, except those in NO_HELL.
    leifs: leifs to spend on top of stamina.
    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if hunt not in HUNTS:
        log.error(f"unknown hunt {hunt}, expected one of {', '.join(HUNTS)}")
        return False
    if hunt in NO_HELL:
        log.error(f"{hunt} has no Hunt - Hell, not supported yet")
        return False
    popups = game_popups(GAME)
    running = _running(popups)
    if running is None:
        return False
    if running:
        log.error("a background battle is already running, not starting another")
        return False
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not _pick(hunt, popups, delay, tries):
        return False
    if not tap_until(HELL, QUICK_BATTLING, delay, tries, popups=popups):
        log.error("hunt-team not reached")
        return False
    opened = tap_until(BACKGROUND, [DIALOG_TITLE, AUTO_TITLE], delay, tries, popups=popups)
    if not opened:
        log.error("Background Battling dialog not opened")
        return False
    if opened[0] == str(AUTO_TITLE):
        # A battle running opens its progress view, with Stop, instead.
        log.error("a background battle is already running, closing its progress view")
        tap_until(RUNNING_CLOSE, QUICK_BATTLING, delay, tries, popups=popups)
        return False
    _tick_energy(popups, delay, tries)
    start = _set_count(leifs, delay)
    if start is None:
        return False
    if start:
        if not _start(popups, delay, tries):
            return False
        log.info(f"background battle started on {hunt}")
    elif not tap_until(DIALOG_CLOSE, QUICK_BATTLING, delay, tries, popups=popups):
        log.error("Background Battling dialog not closed")
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    log.info("done, back in lobby")
    return True


def _cut(screen, box):
    x, y, w, h = box
    return screen[y:y + h, x:x + w].astype(np.int16)


def _changed(a, b, box):
    return float(np.abs(_cut(a, box) - _cut(b, box)).mean())


def _running(popups, attempts=3):
    """True if the lobby's HUD clock is spinning, False if it's still or
    missing, None if the HUD wasn't seen. Two frames SPIN_GAP apart, both with
    the HUD up, since the lobby hides it again within seconds."""
    for attempt in range(1, attempts + 1):
        if not lobby.run():
            log.error("lobby not reached")
            return None
        first = past_black()
        if open_popup(popups, first):
            continue    # Rule 1: the lobby routine closes it on the next attempt
        time.sleep(SPIN_GAP)
        second = capture()
        if locate(lobby.MAIN_MENU, first) and locate(lobby.MAIN_MENU, second):
            change = _changed(first, second, CLOCK_BOX)
            log.debug(f"clock change {change:.1f}")
            return change >= SPIN_MIN
        log.debug(f"HUD not showing, attempt {attempt}/{attempts}")
    log.error(f"HUD not seen in {attempts} attempts")
    return None


def _pick(hunt, popups, delay, tries):
    """Make `hunt` the chosen hunt. True once its reward icon shows."""
    target = HUNTS.index(hunt)
    for _ in range(len(HUNTS) + tries):
        screen = past_black()
        if locate(_reward(hunt), screen):
            log.info(f"{hunt} chosen")
            return True
        if not locate(TITLE, screen):
            log.error(f"{MENU} not on screen")
            return False
        showing = [i for i, name in enumerate(HUNTS) if locate(_card(name), screen)]
        if not showing:
            log.error("no hunt card on screen")
            return False
        nearest = min(showing, key=lambda i: abs(i - target))
        name = HUNTS[nearest]
        if not locate(_reward(name), screen):
            log.debug(f"tapping {name}, nearest showing card to {hunt}")
            if not tap_until(_card(name), _reward(name), delay, tries, popups=popups):
                log.error(f"{name} not chosen")
                return False
            continue
        # The nearest card is already chosen, so the next one toward the target
        # shows at most partly, too little for its label to match: tap a card
        # step past the chosen label, kept on screen.
        step = 1 if target > nearest else -1
        nxt = HUNTS[nearest + step]
        x, y, _ = locate(_card(name), screen)
        x, y = tap(x, min(max(y + step * CARD_STEP, CARD_Y_MIN), CARD_Y_MAX))
        log.debug(f"tapping {nxt} at ({x}, {y}), past {name}")
        if not wait_until(lambda: locate(_reward(nxt), capture()), delay):
            log.warning(f"{nxt} not chosen after a tap past {name}, retrying")
    log.error(f"{hunt} not reached")
    return False


def _tick_energy(popups, delay, tries):
    """Tick Use Owned Energy First unless it already is. Greyed out, it
    doesn't tick: that's no failure, the run goes on without it."""
    if locate(TICKED, past_black()):
        return
    if tap_until(ENERGY, TICKED, delay, tries, popups=popups):
        log.info("Use Owned Energy First ticked")
    else:
        log.warning("Use Owned Energy First not ticked (greyed out?), going on without it")


def _step(button, delay):
    """Tap +1 or -1 once. True if the count changed, False if it was at the
    end of its range, None if the button wasn't there."""
    screen = past_black()
    hit = locate(button, screen)
    if not hit:
        log.error(f"{button.name} not on screen")
        return None
    x, y = tap(*hit[:2])
    log.debug(f"{button.name} tap at ({x}, {y})")
    return wait_until(lambda: _changed(screen, capture(), COUNT_BOX) >= COUNT_CHANGED, delay) is not None


def _set_count(leifs, delay):
    """Set Leifs to be Used to the most stamina-only steps, plus `leifs` leif
    steps. True to start, False when the first step already costs a leif and
    no leifs were asked for (not enough stamina), None on failure."""
    stamina = 1    # the dialog opens on 1
    while locate(LEIF_ZERO, past_black()):
        moved = _step(PLUS, delay)
        if moved is None:
            return None
        if not moved:
            log.info(f"count at its max after {stamina} stamina steps, no leif needed")
            return True
        stamina += 1
    stamina -= 1    # the last step is the first that costs a leif
    if leifs == 0:
        if stamina == 0:
            log.info("first step already costs a leif, not enough stamina, nothing to do")
            return False
        if not _step(MINUS, delay) or not locate(LEIF_ZERO, past_black()):
            log.error("leif cost not back to 0 after -1")
            return None
        log.info(f"{stamina} stamina steps, no leifs")
        return True
    for i in range(1, leifs):
        moved = _step(PLUS, delay)
        if moved is None:
            return None
        if not moved:
            log.warning(f"count at its max after {i}/{leifs} leifs, starting with those")
            break
    log.info(f"{stamina} stamina steps and up to {leifs} leifs")
    return True


def _start(popups, delay, tries):
    """Tap Start, then Confirm. True once hunt-team shows again."""
    if not tap_until(START, START_QUESTION, delay, tries, popups=popups):
        log.error("Start's confirm dialog not shown")
        return False
    if not tap_until(START_CONFIRM, QUICK_BATTLING, delay, tries, popups=popups):
        log.error("hunt-team not back after Confirm")
        return False
    return True


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--hunt", default="wyvern", choices=HUNTS)
    p.add_argument("--leifs", type=int, default=0)
    p.add_argument("--debug", action="store_true")
    a = p.parse_args()
    setup(debug=a.debug)
    sys.exit(0 if run(hunt=a.hunt, leifs=a.leifs) else 1)
