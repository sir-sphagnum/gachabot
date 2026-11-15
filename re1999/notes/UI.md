# Reverse: 1999 UI notes

How Reverse: 1999 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `re1999/templates/` (see the map skill for the scheme). `re1999/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `re1999/`.

## start-screen (`re1999/templates/start-screen/`)

The title screen: "REVERSE 1999" over a café front, with START at the bottom centre and three round icons on the right (Repair at the top). Tapping START (`btn_start-screen_lobby_883-789-140-28.png`) starts the game.

- Launch: black for a few seconds, then a loading screen with a progress bar and "Loading (no data will be used during loading), please wait ..." (~20 s), then the start screen. The loading screen also has a Repair button at the top right. Nothing identifies it yet, so the lobby routine, run while it shows, presses Back on it; start it with `start_screen`, which waits for the start screen instead.
- A thin orbit (an ellipse with a dot) spins around START and crosses its letters, so the template is a PNG whose alpha keeps only the letters (brightness above 180, grown by 1 px, the dot's spot over the T cleared). It scored 1.00 on its source and 0.97 on a capture with the orbit elsewhere, at most 0.18 on every other screen.
- `re1999/routines/start_screen.py` taps START and waits for the lobby (`python -m re1999.bot start_screen`). From a force-stop, `python -m re1999.bot start start_screen` took ~21 s to the start screen and 7 s more to the lobby, on a launch with no popups (the day's rewards already claimed).
- After START: a story loading screen (dark, a film strip and a line of lore text) for ~10 s, then on the first launch of the day the popups and dialogs below, in this order: obtained (login reward), the lobby's checkin card, event-login, obtained (event reward, if claimed), then the lobby.

## lobby (`re1999/templates/start-screen/lobby/`)

Four states seen so far: active (`screen.png`), checkin (`screen-checkin.png`), checkin-calendar (`screen-checkin-calendar.png`) and quit (`screen-quit.png`). `re1999/routines/lobby.py` reaches the active lobby from anywhere (`python -m re1999.bot lobby`); its `DIALOGS` closes the other three.

- **active**: identified by the Crew button (`info_lobby_crew_1646-591-138-124.png`, framed silhouette right of centre): 1.00 on the lobby, at most 0.76 elsewhere (the blurred lobby behind the checkin card). The centre character and the event banners at the top right change, so they aren't used.
- **quit**: "Notice / Quit the Game?" with CANCEL and CONFIRM, a white system-style dialog over the dimmed lobby. Android Back in the lobby opens it, so the lobby routine opens it whenever it presses Back one time too many.
  - Identified by "Quit the Game?" (`info_lobby_quit-text_584-496-172-38.png`): 1.00 on the dialog, at most 0.15 elsewhere.
  - Closed by CANCEL (`btn_lobby_quit-cancel_1114-596-100-42.png`): 1.00 on the dialog, at most 0.22 elsewhere. Never tap CONFIRM: it quits the game.
  - Crew still matches through the dim (1.00), so the routine checks for this dialog before trusting Crew.
- An eye icon at the bottom left, ~(118, 990), probably hides the HUD. Untested: if it does, Crew goes with it, and the lobby needs a scene element too, as E7 pairs its barrel with the main-menu icon.
- **checkin**: the daily sign-in card (date, a line of trivia, "Today's Rewards", "Days signed in: n" and milestone rewards) over the blurred lobby, shown once a day after the first obtained popup. Today's reward is already claimed when it shows. It's a lobby state rather than a common popup because it only shows as the lobby opens.
  - Identified by "Today's Rewards" (`info_lobby_checkin-text_864-542-188-40.png`): 1.00 on the card, at most 0.24 elsewhere.
  - The orange calendar icon at the card's top right (`btn_lobby_checkin-calendar_1094-70-92-62.png`) doesn't close it: it widens the card into checkin-calendar. The lobby routine uses it as the card's way out anyway, since it's the one control tried on the card.
- **checkin-calendar**: the full month calendar, every day's reward and CLAIMED stamps, with the card's lower half at the left and an orange swap-arrows button at the bottom right.
  - Identified by "Today's Rewards" at its new spot (`info_lobby_checkin-calendar-text_180-532-190-42.png`): 1.00 here, at most 0.07 elsewhere.
  - Closed by a tap on the screen's top-right corner (`btn_lobby_checkin-close_1830-10-80-60.png`, outside the panel), which leads to event-login. Whether the same tap closes the narrow checkin card wasn't tried. The crop is just blurred background, so it marks a tap spot only, never a state; the lobby routine taps the point (1870, 40) instead of locating the crop.

## obtained popup (`re1999/templates/common/popups/obtained/`)

"Obtained" with a gift icon at the top and the items received in the middle, over a dark blurred backdrop. Shows for login rewards and after claiming one (e.g. an event-login card), so it can come up over many screens.

- Identified by the "Obtained" title (`info_obtained_title_872-178-176-46.png`): 1.00 and 0.99 on the two seen (different items), at most 0.20 elsewhere.
- Closed by tapping the title (`btn_obtained_close_...`, the same box). There's no close button.

## event-login popup (`re1999/templates/common/popups/event-login/`)

An event's sign-in panel: event title and time left at the top left, a row of day cards with their rewards, a character at the right and a thin X at the top right. Seen as "Rekindled! Games of the Summer-Gold Sea"; the title and art change with each event.

- Today's card has an orange underline and is tapped to claim it (`screen-claim.png`), which opens obtained; claimed cards turn grey with a tick. It isn't cropped, since which card is today's moves daily.
- Identified and closed by the X (`info_event-login_x_1745-180-56-54.png`, `btn_event-login_close_...`): 1.00 on the panel before and after claiming, at most 0.46 elsewhere (the start screen). Whether the X stays at this spot for other events is unknown.
- The lobby routine closes it with the X like any popup, so a day's card it meets unclaimed stays unclaimed.

## mail (`re1999/templates/start-screen/lobby/mail/`)

The mailbox: a list of mails at the left (Claim All, Delete Read), the open mail at the right with its attachments and Claim. Opened by Mail at the lobby's top left (`btn_lobby_mail_70-232-96-108.png`), identified by its "Mail" title (`info_mail_title_172-136-104-54.png`: 1.00 here, at most 0.13 elsewhere). Android Back closes it to the lobby.
