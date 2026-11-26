"""Reverse: 1999 bot entry point.

Usage: python -m re1999.bot start          launch Reverse: 1999 (or bring it to the front), closing any other running game
       python -m re1999.bot stop           force-stop Reverse: 1999
       python -m re1999.bot back           close the current menu
       python -m re1999.bot ROUTINE ...    run routines from re1999.routines.ROUTINES, in order

Add --debug to also log each tap and wait.
"""

import sys

from core import device
from core.input import back as press_back
from core.log import logger, setup
from re1999.config import BACK_KEY, GAME
from re1999.routines import ROUTINES

log = logger(__file__)


def start():
    """Launch Reverse: 1999. Returns True once it is in focus."""
    return device.start_game(GAME)


def stop():
    return device.stop_game(GAME)


def back():
    """Close the current menu (BACK_KEY; see re1999.config)."""
    press_back(BACK_KEY)


COMMANDS = {"start": start, "stop": stop, "back": back}


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if a != "--debug"]
    setup(debug="--debug" in sys.argv[1:], run=f"{__spec__.name}-{'-'.join(names)}")
    unknown = [n for n in names if n not in COMMANDS and n not in ROUTINES]
    if not names or unknown:
        if unknown:
            print(f"Unknown: {', '.join(unknown)}")
        print(__doc__)
        print("Routines:", ", ".join(ROUTINES) or "(none yet)")
        sys.exit(1)
    for name in names:
        # Routines run with the emulator's memory kept in check (core.device.with_room).
        result = COMMANDS[name]() if name in COMMANDS else device.with_room(GAME, ROUTINES[name])
        if result is False:
            log.error(f"{name}: failed")
            sys.exit(1)
        log.info(f"{name}: ok")
