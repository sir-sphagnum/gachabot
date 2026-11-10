"""Get to the E7 lobby with its HUD showing, from wherever the game is.

Usage: python -m e7.routines.lobby

1. If the barrel (big barrel on the wall right of the bar) isn't on screen,
   we're not in the lobby. If we're on the start screen (title screen, "Tap to
   Start"), hand over to the start_screen routine to get past it; otherwise
   press Back. Repeat until the barrel shows.
2. If the barrel is there but the active-lobby icons (main-menu 4-boxes and
   Sanctuary) aren't, the HUD is hidden: tap the table candle (bottom left)
   until they show.

The start screen is checked before every Back press, as Back does nothing
useful there (see e7/routines/start_screen.py for how it's recognised).

The quit dialog ("Are you sure you want to quit the game?") is checked before
every Back press and every candle tap: one Back too many in the lobby opens
it, and the lobby (barrel included) shows dimmed behind it, so the candle tap
would do nothing. When it's up, tap its Cancel button (never Confirm, which
quits the game). Its templates are in common/popups/quit-game/.

The lobby has two states. Active: the HUD shows, with the 4-boxes icon (top
right) and Sanctuary (left). Rest: the HUD is hidden; the lobby drops back to
this after a few idle seconds. The barrel is part of the scene, so it shows in
both, and it is what tells the lobby apart from screens without a HUD. It
matches by day and by night (the scene's lighting changes, which is why the
lit/unlit table candle can't be the indicator). Neither HUD icon is enough
alone: the 4-boxes icon also shows on the shop, and Sanctuary shows on the
main-menu panel drawn over the lobby (where the barrel shows through too).
Tapping the candle's spot wakes the HUD, and also closes that panel.
"""

import sys

from core.device import wait_until
from core.input import back, capture, tap
from core.nav import close_popup, locate, open_popup
from core.tree import load_popups
from e7.config import BACK_KEY, GAME, TEMPLATES_DIR
from e7.routines import start_screen

LOBBY = TEMPLATES_DIR / "start-screen" / "lobby"
BARREL = LOBBY / "info_lobby_barrel_1240-140-80-120.png"       # scene: both states, day and night
ACTIVE = [LOBBY / "btn_lobby_main-menu_1847-20-45-58.png",      # HUD: all must show
          LOBBY / "info_lobby_sanctuary_27-246-112-86.png"]
WAKE = (198, 975)  # table candle, bottom left: tapping it wakes the HUD (no HUD button there)
QUIT = "quit-game"  # popup in common/popups/: "quit the game?", closed with Cancel


def run(backs=10, taps=5, delay=1.5, verbose=True):
    """Return True once the active lobby is on screen, False if it couldn't get there.

    backs: maximum Back presses to reach the lobby.
    taps: maximum taps to wake its HUD.
    delay: seconds to keep checking the screen after each press or tap.
    """
    say = print if verbose else (lambda *a: None)

    quit_dialog = {QUIT: load_popups(GAME)[0][QUIT]}

    def cancel_quit(screen):
        """If the quit dialog is up on `screen`, tap Cancel. Returns a fresh
        capture once it's gone, False if it won't close, None if it wasn't up."""
        if not open_popup(quit_dialog, screen):
            return None
        say("Quit dialog is up; tapping Cancel")
        if not close_popup(quit_dialog[QUIT], delay, say=say):
            say("Quit dialog didn't close")
            return False
        return capture()

    screen = capture()
    presses = 0
    started = False
    while True:
        cancelled = cancel_quit(screen)
        if cancelled is False:
            return False
        if cancelled is not None:
            screen = cancelled
            continue
        if locate(BARREL, screen):
            break
        if start_screen.at_start_screen(screen):
            if started:
                say("Back on the start screen after getting past it once")
                return False
            started = True
            start_screen.run(appear=delay, verbose=verbose)
            screen = capture()
            continue
        if presses == backs:
            say(f"Lobby barrel not seen after {backs} Back presses")
            return False
        presses += 1
        say(f"Not in the lobby; Back {presses}/{backs}")
        back(BACK_KEY)
        screen = wait_until(lambda: _with(BARREL), delay) or capture()

    for attempt in range(1, taps + 1):
        cancelled = cancel_quit(screen)
        if cancelled is False:
            return False
        screen = cancelled or screen
        if is_active(screen):
            say("Lobby is active")
            return True
        if locate(BARREL, screen):
            say(f"Lobby HUD hidden; tap {attempt}/{taps} at {WAKE}")
            tap(*WAKE)
        else:
            say(f"Tap {attempt}/{taps} skipped: lobby barrel not on screen")
        screen = wait_until(_active_screen, delay) or capture()

    if is_active(screen):
        say("Lobby is active")
        return True
    say(f"Lobby HUD not shown after {taps} taps")
    return False


def is_active(screen=None):
    """True when the lobby is on screen with its HUD showing."""
    screen = capture() if screen is None else screen
    return all(locate(t, screen) for t in [BARREL, *ACTIVE])


def _with(template):
    """A fresh capture if `template` is on it, else None."""
    screen = capture()
    return screen if locate(template, screen) else None


def _active_screen():
    screen = capture()
    return screen if is_active(screen) else None


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
