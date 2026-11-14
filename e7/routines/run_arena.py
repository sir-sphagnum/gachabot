"""Fight arena opponents on auto until the flags run out.

Usage: python -m e7.routines.run_arena [--fights N] [--debug]

1. Go to arena, the opponent list (core.nav.goto).
2. Until the top bar's flag counter shows 0 (or N fights are done):
   - pick the first opponent row that isn't red (an opponent already fought
     this list). If all three are red, tap Refresh while it shows "Free" and
     Confirm its dialog while Confirm says Free (else Cancel and stop); if
     Refresh doesn't show Free (on cooldown), stop;
   - tap the row, check Challenge lit up, tap Challenge until arena-team's
     Start shows, tap Start until it's gone (a ~7 s load follows). If Start
     opens Purchase Flags instead, the flags are spent: Cancel and stop;
   - wait for the battle view's Auto icon and tap it: every battle starts
     with auto off;
   - wait for the results (Confirm and "Victory Points"), tap Confirm until
     the list is back.
3. Go back to the lobby (the lobby routine).

--fights N stops after N fights. Without it the run needs the flag-0 image
(info_arena_flags-0_*.png): with neither, the routine refuses to start rather
than rely on Purchase Flags alone to stop it.
"""

import sys
import time

import cv2

from core.device import wait_until
from core.input import capture, tap
from core.log import logger, setup
from core.nav import close_popup, dialog, game_popups, goto, locate, open_popup, past_black, tap_until
from e7.config import GAME, TEMPLATES_DIR
from e7.routines import lobby

log = logger(__file__)

MENU = "arena"
ARENA = TEMPLATES_DIR / "start-screen" / "lobby" / "main-menu" / "arena-landing" / MENU
TEAM = ARENA / "arena-team"
BATTLE = TEAM / "arena-battle"
DEFENSE = ARENA / "info_arena_defense-team_125-785-210-50.png"       # identifies arena
REFRESH_FREE = ARENA / "info_arena_refresh-free_1310-150-90-50.png"  # "Free" on Refresh
# Refresh's dialog: "Would you like to refresh the opponent?", Cancel and a
# green [Free] Confirm. Refreshes past the free one count toward a daily
# limit, so Confirm is tapped only while its pill says Free.
REFRESH_QUESTION = ARENA / "info_arena_refresh-question_695-405-530-50.png"
REFRESH_CONFIRM_FREE = ARENA / "info_arena_refresh-confirm-free_960-722-150-50.png"
REFRESH_CONFIRM = ARENA / "btn_arena_refresh-confirm_1140-715-180-65.png"
REFRESH_DIALOG = dialog(REFRESH_QUESTION, ARENA / "btn_arena_refresh-cancel_600-710-255-75.png")
CHALLENGE = ARENA / "btn_arena_arena-team_775-950-365-85.png"
START = TEAM / "btn_arena-team_arena-battle_1180-960-180-65.png"     # "Start", without the flag count
# Start with no flags opens Purchase Flags. Its Buy spends crystals, so the
# routine only ever taps Cancel. Start still matches (1.00) under its dim.
PURCHASE_FLAGS = dialog(TEAM / "info_arena-team_purchase-flags-title_795-210-330-65.png",
                        TEAM / "btn_arena-team_purchase-flags-cancel_660-790-280-75.png")
PURCHASE = {"purchase-flags": PURCHASE_FLAGS}
AUTO = BATTLE / "btn_arena-battle_auto_1660-18-62-64.png"            # A in a circle of arrows, still (off)
VICTORY_POINTS = BATTLE / "info_arena-battle_victory-points_855-610-210-45.png"
CONFIRM = BATTLE / "btn_arena-battle_arena_1630-950-250-85.png"      # same spot on a win and a defeat

# Opponent rows: tap points and the background strip whose colour tells a
# fought (red) row from a fresh (grey) one. Red minus blue over the strip is
# +45 red, +7..+8 grey, gold highlight or not.
ROW_STEP = 192
ROW_TAP = (720, 350)
ROW_STRIP = (760, 262, 90, 30)
RED_MIN = 25
# Challenge lights up once a row is chosen: green minus blue +29 lit, +10 dim.
# Matching can't tell them apart (0.97 dim).
CHALLENGE_BOX = (800, 960, 315, 65)
LIT_MIN = 20

# The flag-0 image matches white-only: 0.94-1.00 on "0/5", 0.75-0.77 on 10, 9
# and 8 (rounded digits), so it needs more than the usual 0.85. 2-6 weren't
# seen. A miss costs one trip to Purchase Flags, which stops the run too.
ZERO_MIN = 0.90
LOAD_WAIT = 30     # seconds from Start to the battle view (~7 s seen)
BATTLE_WAIT = 600    # seconds from the battle view to the results
AUTO_STILL = 3       # Auto matched this many polls in a row: it isn't spinning, so auto is off
AUTO_RETAPS = 3
NO_FLAGS = "no flags"  # _fight's result when Start opened Purchase Flags


def _flags_zero():
    return next(ARENA.glob("info_arena_flags-0_*.png"), None)


def run(fights=None, delay=1.5, tries=5):
    """Return True once the flags are spent (or `fights` fights are done, or
    no opponent is left and Refresh is on cooldown) and the game is back in
    the lobby; False if it couldn't go on.

    fights: stop after this many fights; None runs until the flag counter
        shows 0, which needs the flag-0 image.
    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not _fights(fights, delay, tries):
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    log.info("done, back in lobby")
    return True


def _fights(fights, delay, tries):
    """Fight until one of run()'s stops. True once stopped there, on arena
    (on arena-team when Purchase Flags stopped it)."""
    zero = _flags_zero()
    if fights is None and zero is None:
        log.error("no flag-0 image and no fight count, not starting")
        return False
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    popups = game_popups(GAME)
    done = 0
    while fights is None or done < fights:
        # Refresh's dialog left open closes like a popup here, but not in
        # tap_until, which would close it while _refresh waits for it.
        screen = _clear({**popups, "refresh": REFRESH_DIALOG}, delay, tries)
        if screen is None:
            return False
        if not locate(DEFENSE, screen):
            log.error(f"{MENU} not on screen")
            return False
        if zero and locate(zero, screen, threshold=ZERO_MIN):
            log.info(f"flags at 0 after {done} fights")
            return True
        row = _free_row(screen)
        if row is None:
            refresh = locate(REFRESH_FREE, screen)
            if not refresh:
                log.info(f"every opponent fought and Refresh on cooldown, stopping after {done} fights")
                return True
            log.info("every opponent fought, refreshing")
            if not _refresh(popups, delay, tries):
                return False
            continue
        result = _fight(row, popups, delay, tries)
        if result == NO_FLAGS:
            log.info(f"flags spent after {done} fights")
            return True
        if not result:
            return False
        done += 1
        log.info(f"fight {done} done")
    log.info(f"{done} fights done")
    return True


def _clear(popups, delay, tries):
    """The current screen with no common popup open, or None if one couldn't
    be closed (Rule 1)."""
    screen = past_black()
    name = open_popup(popups, screen)
    if name:
        log.warning(f"popup_{name} open, closing")
        if not close_popup(name, popups[name], delay, tries):
            log.error(f"popup_{name} not closed")
            return None
        screen = past_black()
    return screen


def _mean(screen, box):
    x, y, w, h = box
    b, g, r = cv2.mean(screen[y:y + h, x:x + w])[:3]
    return r, g, b


def _free_row(screen):
    """Index (0-2) of the first opponent row that isn't red, or None."""
    for i in range(3):
        x, y, w, h = ROW_STRIP
        r, _, b = _mean(screen, (x, y + i * ROW_STEP, w, h))
        if r - b < RED_MIN:
            return i
    return None


def _refresh(popups, delay, tries):
    """Tap Refresh and answer its dialog: Confirm only while its button says
    Free, else Cancel. True once the list shows a fresh row."""
    if not tap_until(REFRESH_FREE, REFRESH_QUESTION, delay, tries, popups=popups):
        log.error("Refresh dialog not shown")
        return False
    if not locate(REFRESH_CONFIRM_FREE, capture()):
        log.error("Refresh not free, cancelling")
        close_popup("refresh", REFRESH_DIALOG, delay, tries)
        return False
    if not tap_until(REFRESH_CONFIRM, DEFENSE, delay, tries, popups=popups):
        log.error(f"{MENU} not back after Refresh")
        return False
    if wait_until(lambda: _free_row(capture()) is not None, delay * tries) is None:
        log.error("opponents still all red after Refresh")
        return False
    return True


def _lit(screen):
    _, g, b = _mean(screen, CHALLENGE_BOX)
    return g - b >= LIT_MIN


def _fight(row, popups, delay, tries):
    """Fight the opponent on `row`. True once back on arena after the
    results, NO_FLAGS if Start opened Purchase Flags (cancelled, so the game
    is on arena-team), False if it couldn't go on."""
    point = (ROW_TAP[0], ROW_TAP[1] + row * ROW_STEP)
    log.info(f"opponent {row + 1}/3, challenging")
    for attempt in range(1, tries + 1):
        tap(*point)
        if wait_until(lambda: _lit(capture()), delay):
            break
        log.debug(f"row tap {attempt}/{tries}: Challenge still dim")
    else:
        log.error(f"Challenge not lit after {tries} row taps")
        return False
    if not tap_until(CHALLENGE, START, delay, tries, popups=popups):
        log.error("arena-team not reached")
        return False
    started = _start(popups, delay, tries)
    if started is not True:
        return started
    if not _auto_on():
        return False
    if not _results(popups, delay, tries):
        return False
    if not tap_until(CONFIRM, DEFENSE, delay, tries, popups=popups):
        log.error(f"{MENU} not back after Confirm")
        return False
    return True


def _start(popups, delay, tries):
    """Tap Start, then wait out the load until Auto shows. True once it
    does, NO_FLAGS if Purchase Flags opened instead (cancelled), else False.
    Start flickers on and off for a second or so after a tap that took, so
    it's tapped again only once the load has had its full time and Start is
    still there."""
    for attempt in range(1, tries + 1):
        screen = _clear(popups, delay, tries)
        if screen is None:
            return False
        if open_popup(PURCHASE, screen):  # Start matches under it (Rule 1)
            return _no_flags(delay, tries)
        hit = locate(START, screen)
        if not hit:
            log.error("Start not on screen")
            return False
        x, y = tap(*hit[:2])
        log.debug(f"Start tap {attempt}/{tries} at ({x}, {y})")
        seen = wait_until(lambda: _battle_or_purchase(capture()), LOAD_WAIT)
        if seen == "purchase":
            return _no_flags(delay, tries)
        if seen:
            log.info("battle started")
            return True
        log.warning(f"no battle view {LOAD_WAIT}s after Start tap {attempt}/{tries}, retrying")
    log.error(f"no battle view after {tries} Start taps")
    return False


def _battle_or_purchase(screen):
    if open_popup(PURCHASE, screen):
        return "purchase"
    return "battle" if locate(AUTO, screen) else None


def _no_flags(delay, tries):
    """Cancel Purchase Flags. NO_FLAGS once it's closed, else False."""
    log.info("Purchase Flags open: no flags left, cancelling")
    if not close_popup("purchase-flags", PURCHASE_FLAGS, delay, tries):
        log.error("Purchase Flags not closed")
        return False
    return NO_FLAGS


def _auto_on():
    """Tap Auto, which every battle starts with off."""
    hit = locate(AUTO, capture())
    if not hit:
        log.error("Auto not on screen")
        return False
    x, y = tap(*hit[:2])
    log.debug(f"Auto tap at ({x}, {y})")
    return True


def _results(popups, delay, tries):
    """Wait for the results' Confirm. While waiting, an Auto icon that matches
    AUTO_STILL polls in a row isn't spinning, so auto is off: tap it again."""
    deadline = time.monotonic() + BATTLE_WAIT
    still = retaps = 0
    while time.monotonic() < deadline:
        screen = _clear(popups, delay, tries)
        if screen is None:
            return False
        if locate(CONFIRM, screen) and locate(VICTORY_POINTS, screen):
            log.info("results showing")
            return True
        hit = locate(AUTO, screen)
        still = still + 1 if hit else 0
        if still >= AUTO_STILL:
            if retaps == AUTO_RETAPS:
                log.error(f"auto still off after {AUTO_RETAPS} more taps")
                return False
            retaps += 1
            log.warning(f"Auto still for {AUTO_STILL} polls, auto off, tapping {retaps}/{AUTO_RETAPS}")
            tap(*hit[:2])
            still = 0
        time.sleep(1)
    log.error(f"no results {BATTLE_WAIT}s after the battle started")
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    setup(debug="--debug" in args)
    n = int(args[args.index("--fights") + 1]) if "--fights" in args else None
    sys.exit(0 if run(fights=n) else 1)
