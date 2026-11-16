"""Collect the Reverse: 1999 wilderness buildings' resources, then go back to the lobby.

Usage: python -m re1999.routines.claim_wilderness [--debug]

In the wilderness, the pan-map icon at the top left swings the camera to the
next building with something to collect, leaving that building's resource
icon at CENTRE; a tap there collects it. The routine repeats pan + tap until
the pan-map icon is gone, which is how the game shows nothing is left, then
taps Home.

The resource icons sit on the 3D map and the camera swings on its own, so
they're tapped as a point right after a pan, never matched. Once the pan-map
icon is gone, another icon (badge 9) moves up into its spot, so the routine
locates pan-map before every tap instead of tapping its point.
"""

import sys
import time

from core.input import capture, tap
from core.log import logger, setup
from core.nav import goto, locate, tap_until
from re1999.config import GAME, TEMPLATES_DIR
from re1999.routines import lobby

log = logger(__file__)

WILDERNESS = TEMPLATES_DIR / "start-screen" / "lobby" / "wilderness"
PAN = WILDERNESS / "btn_wilderness_pan-map_36-288-82-44.png"
HOME = WILDERNESS / "btn_wilderness_lobby_186-42-56-56.png"
CREW = lobby.CREW
CENTRE = (960, 286)  # where a pan leaves the building's resource icon
PAN_WAIT = 2.5  # seconds for the camera to settle after a pan
COLLECT_WAIT = 2  # seconds for the collect toast and badge to update
ROUNDS = 8  # most buildings collected in one run; 2 were ready when mapped


def run(rounds=ROUNDS):
    """Return True once every building is collected and the lobby is up."""
    if not goto(GAME, "wilderness"):
        log.error("wilderness not reached")
        return False
    collected = 0
    while True:
        hit = locate(PAN, capture())
        if not hit:
            break
        if collected == rounds:
            log.warning(f"pan-map still showing after {rounds} collects, going home")
            break
        collected += 1
        log.debug(f"pan {collected}/{rounds} at ({hit[0]}, {hit[1]})")
        tap(hit[0], hit[1])
        time.sleep(PAN_WAIT)
        log.debug(f"collect {collected}/{rounds} at {CENTRE}")
        tap(*CENTRE)
        time.sleep(COLLECT_WAIT)
    log.info(f"{collected} building(s) collected, going home")
    if not tap_until(HOME, CREW, delay=8):
        log.error("lobby not reached")
        return False
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
