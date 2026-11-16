"""Spend every lesson ticket on the rooms of the first area in the Lesson list.

Usage: python -m ba.routines.lesson [--debug]

1. Go to campus (core.nav.goto: the lobby's Lesson button). Its area list
   scrolls on entry, so wait for it to settle, then tap the top row: that
   area's map ("Select Location") opens.
2. Open All Locations. For each room card, in grid order, while the ticket
   count isn't 0: tap the card (Location Info opens; a locked card opens
   nothing and is skipped), Start Lesson, close any "Relationship rank up!"
   popups (a common popup, one per student who ranked up), Confirm the
   Lesson Report.
3. Close All Locations (X), Home, then the lobby routine.

No tickets left at the start counts as done, not as a failure.
"""

import sys

from core.input import capture
from core.log import logger, setup
from core.nav import close_popup, dialog, goto, locate, settled, tap_until
from ba.config import GAME, TEMPLATES_DIR
from ba.routines import lobby


log = logger(__file__)

MENU = "campus"
CAMPUS = TEMPLATES_DIR / "start-screen" / "lobby" / MENU
LOCATION = CAMPUS / "location"
# The first row once the list has stopped scrolling; which area it is doesn't
# matter (it was Schale Office).
FIRST_AREA = (1338, 283)
SETTLE = 5          # seconds to wait for the area list to stop scrolling

TITLE = LOCATION / "info_location_title_158-12-300-50.png"
ALL_LOCATIONS = LOCATION / "btn_location_all-locations_1630-970-240-54.png"
ALL_TITLE = LOCATION / "info_location_all-locations-title_810-126-300-52.png"
ALL_CLOSE = LOCATION / "btn_location_all-locations-close_1684-130-46-46.png"
# Just the count's first digit: a crop of the whole "Tickets Owned N/6" line
# scores 0.94+ on every count. This one is 1.00 on 0 and at most 0.84 on 1-6,
# hence the high threshold.
ZERO = LOCATION / "info_location_tickets-zero_1040-210-22-34.png"
ZERO_MATCH = 0.95
# Room card centres in the All Locations grid, row by row. The third row's
# first card (Hangar) was locked in Schale Office.
ROOMS = [(447, 379), (963, 379), (1479, 379),
         (447, 605), (963, 605), (1479, 605),
         (447, 830), (963, 830), (1479, 830)]
INFO_TITLE = LOCATION / "info_location_location-info-title_806-148-310-52.png"
INFO_CLOSE = (1446, 173)
START = LOCATION / "btn_location_start-lesson_816-800-290-54.png"
REPORT_TITLE = LOCATION / "info_location_lesson-report-title_816-184-290-52.png"
REPORT_CONFIRM = LOCATION / "btn_location_report-confirm_864-808-192-56.png"
# The lesson animation and up to two rank-ups took under 10 s; tap_until
# waits LESSON_DELAY per round and Start Lesson is gone once tapped.
LESSON_DELAY = 3
LESSON_TRIES = 8
HOME = LOCATION / "btn_location_lobby_1830-12-54-46.png"


def run(delay=1.5, tries=5):
    """Return True once no ticket is left (or none was) and the game is back
    in the lobby, False if it couldn't finish.

    delay, tries: as in core.nav.tap_until, for each tap.
    """
    if not goto(GAME, MENU):
        log.error(f"{MENU} not reached")
        return False
    if not settled(SETTLE):
        log.debug(f"area list still moving after {SETTLE}s, tapping anyway")
    if not tap_until(FIRST_AREA, TITLE, delay, tries):
        log.error("area map not opened")
        return False
    if not tap_until(ALL_LOCATIONS, ALL_TITLE, delay, tries):
        log.error("all locations not opened")
        return False
    held = 0
    for n, room in enumerate(ROOMS, 1):
        if _no_tickets():
            break
        if not tap_until(room, INFO_TITLE, delay, 1):
            log.info(f"room {n}: no location info, skipping (locked or empty)")
            continue
        if not tap_until(START, REPORT_TITLE, LESSON_DELAY, LESSON_TRIES):
            log.error(f"room {n}: lesson report not shown")
            return False
        if not tap_until(REPORT_CONFIRM, ALL_TITLE, delay, tries):
            log.error(f"room {n}: lesson report not closed")
            return False
        held += 1
        log.info(f"room {n}: lesson held")
    if not _no_tickets():
        log.warning(f"tickets left after {held} lessons: no unlocked room left")
    elif not held:
        log.info("no tickets left, nothing to do")
    if not close_popup("all-locations", dialog(ALL_TITLE, ALL_CLOSE), delay, tries):
        log.error("all locations not closed")
        return False
    if not tap_until(HOME, lobby.CAMPAIGN, delay, tries):
        log.warning("home tap didn't reach the lobby, running the lobby routine")
    if not lobby.run():
        log.error("lobby not reached")
        return False
    return True


def _no_tickets():
    return bool(locate(ZERO, capture(), ZERO_MATCH))


if __name__ == "__main__":
    setup(debug="--debug" in sys.argv[1:], run=__spec__.name)
    sys.exit(0 if run() else 1)
