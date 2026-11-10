"""E7 bot entry point.

Usage: python -m e7.bot start          launch E7 (or bring it to the front), fullscreen
       python -m e7.bot stop           force-stop E7
       python -m e7.bot back           close the current menu
       python -m e7.bot ROUTINE ...    run routines from e7.routines.ROUTINES, in order
"""

import sys

from core import device
from core.input import back as press_back
from e7.config import BACK_KEY, GAME
from e7.routines import ROUTINES


def start():
    """Launch E7 fullscreen. Returns True once it is in focus and fullscreen."""
    return device.start_game(GAME, fullscreen=True)


def stop():
    return device.stop_game(GAME)


def back():
    """Close the current menu (Escape, not Android Back; see e7.config)."""
    press_back(BACK_KEY)


COMMANDS = {"start": start, "stop": stop, "back": back}


if __name__ == "__main__":
    names = sys.argv[1:]
    unknown = [n for n in names if n not in COMMANDS and n not in ROUTINES]
    if not names or unknown:
        if unknown:
            print(f"Unknown: {', '.join(unknown)}")
        print(__doc__)
        print("Routines:", ", ".join(ROUTINES) or "(none yet)")
        sys.exit(1)
    for name in names:
        result = (COMMANDS.get(name) or ROUTINES[name])()
        print(f"{name}: {'ok' if result is not False else 'failed'}")
        if result is False:
            sys.exit(1)
