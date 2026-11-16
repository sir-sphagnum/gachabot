"""Tap the Reverse: 1999 lobby character a few times (raises Bond).

Usage: python -m re1999.routines.lobby_interact [--debug]

The character is tapped as a point, not found by matching: which character
stands in the lobby changes. Each tap plays a voice line and may show a
"Bond Increased" toast; neither is checked. The routine succeeds once the
lobby is still up after the last tap, which the lobby routine confirms
(popups closed before trusting Crew, Rule 1).
"""

import sys
import time

from core.input import tap
from core.log import logger, setup
from core.nav import goto
from re1999.config import GAME
from re1999.routines import lobby

log = logger(__file__)

CHARACTER = (960, 540)  # middle of the screen, the character's chest
TAPS = 3
GAP = 3  # seconds between taps, for the voice line to play


def run(taps=TAPS, gap=GAP):
    """Return True once the character was tapped `taps` times and the lobby is up."""
    if not goto(GAME, "lobby"):
        log.error("lobby not reached")
        return False
    for i in range(1, taps + 1):
        log.debug(f"tap {i}/{taps} at {CHARACTER}")
        tap(*CHARACTER)
        time.sleep(gap)
    if not lobby.run():
        log.error("lobby not shown after tapping")
        return False
    log.info(f"character tapped {taps} times")
    return True


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
