# Reverse: 1999 UI notes

How Reverse: 1999 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `re1999/templates/` (see the map skill for the scheme). `re1999/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `re1999/`. Patterns Reverse: 1999 shares with other games are in `core/notes/UI.md`, cited here as "(common: <section>)".

## start-screen (`re1999/templates/start-screen/`)

The title screen: "REVERSE 1999" over a café front, with START at the bottom centre and three round icons on the right (Repair at the top). Tapping START (`btn_start-screen_lobby_883-789-140-28.png`) starts the game.

- Identified by the logo (`info_start-screen_logo_462-350-1000-182.png`, masked to its letters), not by START: the screen also shows without START. 1.00 on every start-screen capture, with START or not, at most 0.09 elsewhere.
- START fades in ~3 s after the screen appears. At a tap (on START or anywhere) START and the icons go but the logo stays for ~20 s while the game logs in, then the story loading screen follows. So the logo without START is either the fade-in or a game already starting; `start_screen` waits up to 20 s for START and, if it never comes, goes on to wait for the lobby.

- Launch: black, then ~4 s of splash art and a fade-in (random art, nothing to match), then a loading screen with a progress bar and "Loading (no data will be used during loading), please wait ..." (~20 s), then the start screen. The loading screen also has a Repair button at the top right. It's `common/loading/` (`screen.png`), identified by its "Loading … please wait" line (`info_loading_launch-text_616-972-688-44.png`, masked to the letters in case the art behind it changes between launches): 1.00 on it, at most 0.12 elsewhere. The lobby routine waits while it shows instead of pressing Back, and for the first 45 s of the game's process (`core.device.uptime`) it waits on any screen it doesn't know: Backs on the splash and the start screen's fade-in opened the quit dialog.
- START has an intro animation: a ring of small text ("MAKE GOOD USE OF THIS UMBRELLA") turns around it before the orbit settles. The letter-masked START already scores 0.93 then, but the game ignores taps until it ends; a tap at that point leaves the start screen up with START back on it. So `start_screen` counts START as gone only once it has been missing for 1.5 s, and taps again if START comes back while it waits for the lobby. Three relaunches in a row after that change didn't hit the intro, so the retap was tested only on recorded frames.
- A thin orbit (an ellipse with a dot) spins around START and crosses its letters, so the template is a PNG whose alpha keeps only the letters (brightness above 180, grown by 1 px, the dot's spot over the T cleared). It scored 1.00 on its source and 0.97 on a capture with the orbit elsewhere, at most 0.18 on every other screen.
- `re1999/routines/start_screen.py` taps START and waits for the lobby (`python -m re1999.bot start_screen`); `python -m core.device restart re1999` runs it and then the lobby routine. From a force-stop, launch to the start screen took ~20 s and START to the lobby ~8 s, on launches with no popups (the day's rewards already claimed). On the one first-launch-of-the-day run so far, the profile state showed after login before checkin and obtained.
- After START: a story loading screen (dark, a film strip and a line of lore text; not mapped, so the lobby routine run during it presses Back) for ~10 s, then on the first launch of the day the popups and dialogs below, in this order: obtained (login reward), the lobby's checkin card, event-login, obtained (event reward, if claimed), then the lobby.

## lobby (`re1999/templates/start-screen/lobby/`)

Five states seen so far: active (`screen.png`), checkin (`screen-checkin.png`), checkin-calendar (`screen-checkin-calendar.png`), profile (`screen-profile.png`) and quit (`screen-quit.png`). `re1999/routines/lobby.py` reaches the active lobby from anywhere (`python -m re1999.bot lobby`); its `DIALOGS` closes the other four.

- **active**: identified by the Crew button (`info_lobby_crew_1646-591-138-124.png`, framed silhouette right of centre): 1.00 on the lobby, at most 0.76 elsewhere (the blurred lobby behind the checkin card). The centre character and the event banners at the top right change, so they aren't used.
- **quit**: "Notice / Quit the Game?" with CANCEL and CONFIRM, a white system-style dialog over the dimmed lobby. Android Back in the lobby opens it, so the lobby routine opens it whenever it presses Back one time too many.
  - Identified by "Quit the Game?" (`info_lobby_quit-text_584-496-172-38.png`): 1.00 on the dialog, at most 0.15 elsewhere.
  - Closed by CANCEL (`btn_lobby_quit-cancel_1114-596-100-42.png`): 1.00 on the dialog, at most 0.22 elsewhere. Never tap CONFIRM: it quits the game.
  - Crew still matches through the dim (1.00), so the routine checks for this dialog before trusting Crew (Rule 1).
- Tapping the centre character, (960, 540), plays a voice line (subtitle at the bottom) and shows a "Bond Increased" toast at the top right, ~(1480, 140) to (1920, 230), over the event banners; the lobby stays active. Whether Bond stops rising after some taps a day is unknown, so nothing checks the toast. The character changes, so it's tapped as a point, never matched. `re1999/routines/lobby_interact.py` taps it 3 times, 3 s apart (`python -m re1999.bot lobby_interact`).
- An eye icon at the bottom left, ~(118, 990), probably hides the HUD. Untested: if it does, Crew goes with it, and the lobby needs a scene identifier too (common: Lobbies).
- **checkin**: the daily sign-in card (date, a line of trivia, "Today's Rewards", "Days signed in: n" and milestone rewards) over the blurred lobby, shown once a day after the first obtained popup. Today's reward is already claimed when it shows. It's a lobby state rather than a common popup because it only shows as the lobby opens.
  - Identified by "Today's Rewards" (`info_lobby_checkin-text_864-542-188-40.png`): 1.00 on the card, at most 0.24 elsewhere.
  - The orange calendar icon at the card's top right (`btn_lobby_checkin-calendar_1094-70-92-62.png`) doesn't close it: it widens the card into checkin-calendar. The lobby routine uses it as the card's way out anyway, since it's the one control tried on the card.
- **checkin-calendar**: the full month calendar, every day's reward and CLAIMED stamps, with the card's lower half at the left and an orange swap-arrows button at the bottom right.
  - Identified by "Today's Rewards" at its new spot (`info_lobby_checkin-calendar-text_180-532-190-42.png`): 1.00 here, at most 0.07 elsewhere.
  - Closed by a tap on the screen's top-right corner (`btn_lobby_checkin-close_1830-10-80-60.png`, outside the panel), which leads to event-login. Whether the same tap closes the narrow checkin card wasn't tried. The crop is just blurred background, so it marks a tap spot only, never a state; the lobby routine taps the point (1870, 40) instead of locating the crop.
- **profile**: the player panel (name, ID, level, DETAIL, a banner carousel, and Atlas, Achievements, Friends, Travel Scrapbook, Notice, Sign-in, Settings, Udimorium) at the left over the blurred lobby, with the lobby character at the right. Opened by the list icon at the lobby's bottom left, ~(117, 805); on the first launch of the day it also showed on its own after login and stayed up, with the day's checkin and obtained still to come behind it. The level badge at the top left opens a different screen, the player card.
  - Identified by the orange DETAIL button (`info_lobby_profile-detail_616-198-112-42.png`): 1.00 here, at most 0.34 elsewhere.
  - Closed to the lobby by a tap on the screen's top-right corner, (1870, 40), the same point as checkin-calendar. Android Back closes it too.

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

## wilderness (`re1999/templates/start-screen/lobby/wilderness/`)

A 3D island with the player's buildings (Dust Bell Tower, Paleohall, Sharpodonty Market, Wishing Spring, …), each with a round resource icon and a % badge. HUD: Back, Home (square) and an info icon at the top left; a currency bar at the top; a column of icons at the left and Dreamwell at the bottom left; Display Paleohall, Medium, Buy, Layout Plan, Place Characters and Edit Wilderness at the right. Opened by Wilderness on the lobby (`btn_lobby_wilderness_1410-600-165-86.png`, cut left of its badges: 1.00 on the lobby, at most 0.30 elsewhere). Entering and leaving both go through a ~5 s loading screen (film strip and a lore line, not mapped); `goto` copes, with two retaps skipped during the load.

- Identified by the "Dreamwell" label (`info_wilderness_dreamwell-text_8-1000-156-40.png`: 1.00 here, 0.99 with the camera elsewhere, at most 0.14 elsewhere) and the "Edit Wilderness" label (`info_wilderness_edit-wilderness-text_1740-995-150-52.png`: at most 0.34 elsewhere). The map behind the HUD swings and changes lighting (teal, sepia), so nothing on it identifies the menu.
- **pan-map** (`btn_wilderness_pan-map_36-288-82-44.png`, the top icon of the left column, cut below its badge): swings the camera to the next building with something to collect, leaving that building's resource icon at ~(960, 286). Its badge seemed to count what's left (6, then 3 after the first collect). Once nothing is left it disappears and the icon below it (badge 9, not mapped) moves up into its spot; pan-map then scores None there, so it's located before every tap, never tapped as a point.
- A tap on a building's resource icon collects it on the spot: a toast at the top right ("Dust +7125 (Vigor Bonus +25%)", "Sharpodonty +3600 …"), the badge drops to 0 % and the resource shows in the top bar. The icons move with the camera, so they're tapped as a point after a pan; the `btn_wilderness_dust-bell-tower-collect_…` and `btn_wilderness_market-collect_…` crops are 3D map art and only record where each was tapped.
- Home (`btn_wilderness_lobby_186-42-56-56.png`) goes back to the lobby: 1.00 here, but the same Home is on every show screen (0.94–0.99 there, see show), so it never identifies wilderness.
- `re1999/routines/claim_wilderness.py` (`python -m re1999.bot claim_wilderness`) pans and taps the centre until pan-map is gone, then goes Home. Its first run met nothing to collect, so the pan-and-collect loop has run only by hand so far.

## show (`re1999/templates/start-screen/lobby/show/`)

The story hub: "The Living and the Rest" at the top left, a row of chapter posters, a reward counter (gift icon, "351/430") at the top right, and a tab bar at the bottom (Story, Reflections, Anecdote, Resource, Insight, Artificial Somnambulism, The Window to Other Worlds, Wanderings). Back and Home at the top left. Opened by the "Enter the Show" ticket under the event banner on the lobby (`btn_lobby_show_1412-442-350-122.png`: 1.00 on the lobby, at most 0.18 elsewhere). The ticket sits under the current event's banner, so it may move or change when the event ends.

- It always opens on the Story tab (three entries in a row), whichever tab was open when it was left. So a routine for another tab taps that tab after every entry.
- Identified by the "The Living and the Rest" title (`info_show_title_190-140-510-60.png`: at most 0.15 elsewhere). The title is the Story tab's latest chapter, so it may change when a new chapter comes out.
- The tab bar is the same on every tab; only the chosen tab's colour and underline change. The Resource tab (`btn_show_resource_692-935-132-100.png`) scores 0.61 on the Resource tab itself, so the tabs never identify which tab is open.
- Home (186, 42) scores 0.94–0.99 on show, resource, both stage screens and wilderness (same art everywhere: common: Shared buttons). It's tapped only once the menu is known.

## resource (`re1999/templates/start-screen/lobby/show/resource/`)

The Resource tab of show: a row of resource-stage records (Pneuma Analysis, The Poussiere, Mintage Aesthetics cut off at the right; more may be further right) over a grey sketch background, with "In-depth Analysis Chances: 2" under Pneuma Analysis.

- Identified by the "In-depth Analysis Chances:" label (`info_resource_analysis-chances_290-795-350-45.png`, cut left of the count: at most 0.48 elsewhere).
- Pneuma Analysis (`btn_resource_pneuma-analysis_160-290-560-440.png`, at most 0.31 elsewhere) and The Poussiere (`btn_resource_the-poussiere_975-290-555-440.png`, at most 0.23 elsewhere) open their stage screens. Whether the row scrolls, and so whether they keep these spots, wasn't tried.

## pneuma-analysis and the-poussiere (`…/show/resource/pneuma-analysis/`, `…/the-poussiere/`)

Stage select for one resource: a full-screen scene (rainy street; overgrown junkyard) with a stage timeline along the bottom, opened scrolled to one stage ("07 / Pneuma Analysis VII", "06 / The Poussiere VI"; probably the highest reached) with the one before it at the left. Back and Home at the top left; Home (`btn_…_lobby_186-42-56-56.png`) goes straight to the lobby.

- pneuma-analysis is identified by the Psychube Shop button at the top right (`info_pneuma-analysis_psychube-shop_1700-30-190-80.png`: at most 0.16 elsewhere), which the-poussiere doesn't have.
- the-poussiere is identified by its focused stage label, "The Poussiere VI" (`info_the-poussiere_stage-label_560-870-335-55.png`: at most 0.30 elsewhere). The label is the stage the timeline opens on, so it breaks once a new stage is reached or the timeline is scrolled; the scene has nothing fixed to use instead.
- The scenes are animated (rain, butterflies), so nothing on them is matched.
