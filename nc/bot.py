"""Project Neural Cloud bot entry point.

Usage: python -m nc.bot start          launch Project Neural Cloud (or bring it to the front), fullscreen, closing any other running game
       python -m nc.bot stop           force-stop Project Neural Cloud
       python -m nc.bot back           close the current menu
       python -m nc.bot ROUTINE ...    run routines from nc.routines.ROUTINES, in order

Add --debug to also log each tap and wait.
"""

import sys

from core import device
from core.input import back as press_back
from core.log import logger, setup
from nc.config import BACK_KEY, GAME
from nc.routines import ROUTINES

log = logger(__file__)


def start():
    """Launch Project Neural Cloud fullscreen. Returns True once it is in focus and fullscreen."""
    return device.start_game(GAME)


def stop():
    return device.stop_game(GAME)


def back():
    """Close the current menu (BACK_KEY; see nc.config)."""
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
        # Routines run with BlueStacks' memory kept in check (core.device.with_room).
        result = COMMANDS[name]() if name in COMMANDS else device.with_room(GAME, ROUTINES[name])
        if result is False:
            log.error(f"{name}: failed")
            sys.exit(1)
        log.info(f"{name}: ok")
