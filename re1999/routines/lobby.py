"""Get to the Reverse: 1999 lobby from wherever the game is.

Usage: python -m re1999.routines.lobby [--debug]

core.nav loads this module by name as the game's lobby routine, the start of
every menu walk, so keep its path and run() returning True on success.

Until the Crew button shows with no popup or lobby dialog over it:
- while the screen is black or a known loading screen
  (re1999/templates/common/loading/) shows, or the game started under LAUNCH
  seconds ago, wait; Back pressed then would be a guess;
- if one of the game's common popups (re1999/templates/common/popups/) or a
  lobby dialog (DIALOGS) is open, close it and look again;
- if the start screen is up, hand over to the start_screen routine (and
  reset the Back count), at most HANDOVERS times;
- otherwise press Back.

Popups and dialogs are checked before Crew because Crew still matches (1.00)
through the quit dialog's dim. Closing one can change where the game is (the
daily check-in card closes into its calendar, which closes into event-login),
so the loop starts over after each. Once the routine has acted (a Back, a
close, a load, a hand-over), Crew counts only after SETTLE seconds with no
popup or dialog: they open a moment after the lobby is drawn (common:
Lobbies), and a Back pressed while a menu was closing opens quit late.

Crew is part of the HUD, so the lobby counts as reached only with its HUD up.
"""

import sys

from core.device import uptime, wait_until
from core.input import back, capture
from core.log import logger, setup
from core.nav import (close_popup, dialog, game_popups, held, loading, locate, open_popup,
                      past_black, past_loading)
from re1999.config import BACK_KEY, GAME, TEMPLATES_DIR
from re1999.routines import start_screen

log = logger(__file__)

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
CREW = LOBBY / "info_lobby_crew_1646-591-138-124.png"
CORNER = (1870, 40)  # top-right corner of the screen, outside the check-in calendar
# For this long after the game's process starts, an unknown screen is a
# launch screen (splash art, fades, the start screen fading in) and the
# routine waits instead of pressing Back: Backs there opened the quit dialog.
LAUNCH = 45  # seconds; launch to start screen took ~20 s
SETTLE = 3  # seconds Crew must show with no popup once the routine has acted
# A start screen that keeps coming back after start_screen ran is one the
# routine can't get past (an error that loops to it): without a cap it would
# hand over forever, since each hand-over resets the Back count.
HANDOVERS = 3

DIALOGS = {
    # "Quit the Game?", opened by Back in the lobby. Cancel, never Confirm.
    "quit": dialog(LOBBY / "info_lobby_quit-text_584-496-172-38.png",
                   LOBBY / "btn_lobby_quit-cancel_1114-596-100-42.png"),
    # Daily sign-in card. Its calendar icon is the one control known to get
    # past it: it opens checkin-calendar, which the corner tap closes.
    "checkin": dialog(LOBBY / "info_lobby_checkin-text_864-542-188-40.png",
                      LOBBY / "btn_lobby_checkin-calendar_1094-70-92-62.png"),
    # The point, not the btn_ crop: that crop is blurred lobby, which changes.
    "checkin-calendar": dialog(LOBBY / "info_lobby_checkin-calendar-text_180-532-190-42.png", CORNER),
    # Player profile, which can show at login. The corner is outside its panels.
    "profile": dialog(LOBBY / "info_lobby_profile-detail_616-198-112-42.png", CORNER),
}


def popups():
    """The game's common popups and the lobby's dialogs, in the form core.nav takes."""
    return {**game_popups(GAME), **DIALOGS}


def run(backs=10, delay=1.5):
    """Return True once the lobby is on screen with its HUD, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby, and maximum popups and
        dialogs closed.
    delay: seconds to keep checking the screen after each press or tap.
    """
    known = popups()
    screen = capture()
    presses = closed = handovers = settles = 0
    acted = False  # a Back, close, load or hand-over since the last look
    while True:
        screen = past_black(screen)
        if loading(GAME, screen):
            screen = past_loading(GAME, screen)
            if screen is None:
                log.error("not reached, stuck on a loading screen")
                return False
            acted = True
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
            acted = True
            continue
        if locate(CREW, screen):
            if acted:
                if settles == backs:
                    log.error(f"lobby never held {SETTLE}s with no popup in {backs} looks")
                    return False
                settles += 1
                log.debug(f"crew showing, watching {SETTLE}s for popups")
                if held(lambda s: _clear_crew(s, known), SETTLE, SETTLE + delay) is None:
                    screen = capture()  # a popup opened, or Crew went: look again
                    continue
            log.info("reached")
            return True
        if start_screen.at_start_screen(screen):
            if handovers == HANDOVERS:
                log.error(f"start screen still showing after {HANDOVERS} hand-overs")
                return False
            handovers += 1
            log.info(f"start screen, handing over ({handovers}/{HANDOVERS})")
            start_screen.run(appear=delay)
            screen = capture()
            presses = 0
            acted = True
            continue
        age = uptime(GAME)
        if age is not None and age < LAUNCH:
            log.debug(f"game started {age}s ago, waiting")
            screen = wait_until(lambda: _known(capture(), known), LAUNCH - age)
            if screen is None:  # not `or`: a capture's truth value raises
                screen = capture()
            acted = True
            continue
        if presses == backs:
            log.error(f"not reached after {backs} backs")
            return False
        presses += 1
        log.debug(f"back {presses}/{backs}")
        back(BACK_KEY)
        acted = True
        screen = wait_until(_crew, delay)
        if screen is None:
            screen = capture()


def _clear_crew(screen, known):
    """`screen` if Crew shows on it with no popup or lobby dialog open, else None."""
    return screen if locate(CREW, screen) and not open_popup(known, screen) else None


def _known(screen, known):
    """`screen` if the routine knows what to do on it, else None."""
    if (loading(GAME, screen) or open_popup(known, screen) or locate(CREW, screen)
            or start_screen.at_start_screen(screen)):
        return screen
    return None


def _crew():
    """A fresh capture if Crew is on it, else None."""
    screen = capture()
    return screen if locate(CREW, screen) else None


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
