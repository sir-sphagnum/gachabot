"""Get past the E7 start screen (title screen, "Tap to Start") into the lobby.

Usage: python -m e7.routines.start_screen

1. Wait for the start screen or the lobby to show (the game may still be
   loading, e.g. right after `python -m e7.bot start`). Already in the lobby:
   done.
2. Tap the "(c) Smilegate. All Rights Reserved." line at the bottom; it marks
   the start screen and starts the game like any tap does. Tap again if the
   start screen is still up after a moment.
3. Wait for the lobby (its wall barrel) while the game loads.

The copyright line is the start screen's indicator. The title art behind it
is animated and its colours change, so the template
(btn_start-screen_lobby_..._white.png) is matched on its white glyphs only,
and its PNG is transparent everywhere except the letters and their dark
outline: core.vision.find ignores transparent pixels, so whatever art shows
between the letters doesn't count.
"""

import sys

from core.device import wait_until
from core.input import capture, tap
from core.nav import locate
from e7.config import TEMPLATES_DIR

START = TEMPLATES_DIR / "start-screen"
COPYRIGHT = START / "btn_start-screen_lobby_805-1023-311-26_white.png"
BARREL = START / "lobby" / "info_lobby_barrel_1240-140-80-120.png"


def run(appear=60, taps=3, delay=3, load=30, verbose=True):
    """Return True once past the start screen and the lobby shows, False otherwise.

    appear: seconds to wait for the start screen (or the lobby) to show up.
    taps: maximum taps on the start screen.
    delay: seconds to wait for the start screen to go after each tap.
    load: seconds to wait for the lobby once the start screen has gone.
    """
    say = print if verbose else (lambda *a: None)

    screen = wait_until(_start_or_lobby, appear)
    if screen is None:
        say(f"Neither the start screen nor the lobby showed within {appear}s")
        return False
    if not at_start_screen(screen):
        say("Not on the start screen; already in the lobby")
        return True

    for attempt in range(1, taps + 1):
        match = locate(COPYRIGHT, screen)
        if not match:
            break
        say(f"On the start screen; tap {attempt}/{taps} at {match[:2]}")
        tap(*match[:2])
        screen = wait_until(_gone, delay) or capture()
    if at_start_screen(screen):
        say(f"Still on the start screen after {taps} taps")
        return False

    say("Left the start screen; waiting for the lobby")
    if wait_until(lambda: locate(BARREL, capture()), load):
        say("In the lobby")
        return True
    say(f"Lobby barrel not seen {load}s after leaving the start screen")
    return False


def at_start_screen(screen=None):
    """True when the start screen is on screen (its copyright line shows)."""
    screen = capture() if screen is None else screen
    return bool(locate(COPYRIGHT, screen))


def _start_or_lobby():
    screen = capture()
    return screen if at_start_screen(screen) or locate(BARREL, screen) else None


def _gone():
    screen = capture()
    return None if at_start_screen(screen) else screen


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
