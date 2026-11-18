"""Get to the Blue Archive lobby from wherever the game is.

Usage: python -m ba.routines.lobby [--debug]

core.nav loads this module by name as the game's lobby routine, the start of
every menu walk, so keep its path and run() returning True on success.

Until Campaign shows with no popup over it:
- while the screen is black or a "Now Loading" screen
  (ba/templates/common/loading/) shows, or the game started under LAUNCH
  seconds ago, wait; Back pressed then would be a guess;
- if one of the game's common popups (ba/templates/common/popups/) is open,
  close it and look again;
- if the start screen is up, hand over to the start_screen routine (and
  reset the Back count);
- if the lobby is idle with its HUD hidden (REST), tap the art to wake it
  (wake());
- otherwise press Back.

Popups are checked before Campaign because neither news nor new-products
covers it, so it still matches (1.00) under them. Closing one can open the
next (news closes into new-products), so the loop starts over after each,
and once Campaign shows after a load or a close the routine watches SETTLE
seconds more: news shows ~2 s after Campaign does.

Campaign is part of the HUD, so the lobby counts as reached only with its
HUD up.
"""

import sys

from core.device import uptime, wait_until
from core.input import back, capture, tap
from core.log import logger, setup
from core.nav import close_popup, game_popups, loading, locate, open_popup, past_black, past_loading
from ba.config import BACK_KEY, GAME, TEMPLATES_DIR
from ba.routines import start_screen

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
CAMPAIGN = LOBBY / "info_lobby_campaign_1728-996-156-46.png"
# The idle lobby (HUD hidden, art zoomed in): the hanging sign top right,
# 1.00 on three idle captures, at most 0.47 elsewhere. Back does nothing
# there; a tap on the art brings the HUD back.
REST = LOBBY / "info_lobby_rest-sign_1530-90-320-370.png"
WAKE = (1500, 600)  # a spot of the art with no HUD button under it
# For this long after the game's process starts, an unknown screen is a
# launch screen (publisher logos, fades) and the routine waits instead of
# pressing Back.
LAUNCH = 45  # seconds; launch to start screen took ~20 s
SETTLE = 4  # seconds to watch for a popup once Campaign shows after a change


def run(backs=10, delay=1.5):
    """Return True once the lobby is on screen with its HUD, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby, and maximum popups closed.
    delay: seconds to keep checking the screen after each press or tap.
    """
    known = game_popups(GAME)
    screen = capture()
    presses = closed = 0
    changed = False  # a load or a popup close since the last look
    while True:
        screen = past_black(screen)
        if loading(GAME, screen):
            screen = past_loading(GAME, screen)
            if screen is None:
                log.error("not reached, stuck on a loading screen")
                return False
            changed = True
            continue
        popup = open_popup(known, screen)
        if popup:
            if closed == backs:
                log.error(f"popups still showing after closing {backs}")
                return False
            closed += 1
            log.warning(f"popup_{popup} open, closing")
            if not close_popup(popup, known[popup], delay):
                log.error(f"popup_{popup} not closed")
                return False
            screen = capture()
            changed = True
            continue
        if locate(CAMPAIGN, screen):
            if changed:
                changed = False
                log.debug(f"campaign showing, watching {SETTLE}s for popups")
                late = wait_until(lambda: _popup(known), SETTLE)
                if late is not None:
                    screen = late
                    continue
            log.info("reached")
            return True
        if start_screen.at_start_screen(screen):
            log.info("start screen, handing over")
            start_screen.run(appear=delay)
            screen = capture()
            presses = 0
            changed = True
            continue
        if locate(REST, screen):
            if presses == backs:
                log.error(f"HUD not woken after {backs} taps")
                return False
            presses += 1
            screen = wake(delay)
            changed = True
            continue
        age = uptime(GAME)
        if age is not None and age < LAUNCH:
            log.debug(f"game started {age}s ago, waiting")
            screen = wait_until(lambda: _known(capture(), known), LAUNCH - age)
            if screen is None:  # not `or`: a capture's truth value raises
                screen = capture()
            continue
        if presses == backs:
            log.error(f"not reached after {backs} backs")
            return False
        presses += 1
        log.debug(f"back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(_campaign, delay)
        if screen is None:
            screen = capture()


def wake(delay=1.5):
    """Tap the idle lobby's art once and return the screen after: Campaign
    once the HUD shows, else the last capture after `delay` seconds."""
    x, y = tap(*WAKE)
    log.info(f"lobby idle, waking HUD at ({x}, {y})")
    screen = wait_until(_campaign, delay)
    return capture() if screen is None else screen


def _known(screen, known):
    """`screen` if the routine knows what to do on it, else None."""
    if (loading(GAME, screen) or open_popup(known, screen) or locate(CAMPAIGN, screen)
            or locate(REST, screen)
            or start_screen.at_start_screen(screen)):
        return screen
    return None


def _popup(known):
    """A fresh capture if a popup is open on it, else None."""
    screen = capture()
    return screen if open_popup(known, screen) else None


def _campaign():
    """A fresh capture if Campaign is on it, else None."""
    screen = capture()
    return screen if locate(CAMPAIGN, screen) else None


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
