# Blue Archive UI notes

How Blue Archive menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `ba/templates/` (see the map skill for the scheme). `ba/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `ba/`.

## start-screen (`ba/templates/start-screen/`)

The title screen: character art, "TOUCH TO START" in a bar at the bottom centre, Notice and Menu buttons bottom left.

- Identified by Notice (`info_start-screen_notice_42-862-116-52.png`) and Menu (`info_start-screen_menu_42-930-110-54.png`): 1.00 on the start screen, at most 0.15 elsewhere. Not by "TOUCH TO START", which pulses.
- Tapping the TOUCH TO START spot (`btn_start-screen_lobby_795-918-330-42.png`, centre (959, 940)) starts the game: 1.00 on its source, at most 0.31 elsewhere. As a match it's unreliable because of the pulse; tap it as a point.
- After the tap, "Now Loading . . ." screens show before the lobby: full-screen art that changes from load to load, with "Now Loading . . ." and a rabbit icon bottom right. `ba/templates/common/loading/info_loading_now-loading_1388-968-292-52.png` is the words without the animated dots, alpha-masked to the pixels that were the same on two loads with different art (42% of the box): 0.96 and 1.00 on those two, no match on any other saved screen. Art not seen yet may need it remasked.
- Launch to start screen took ~20 s on four cold starts; start screen to lobby 8–23 s.
- Automated by `ba/routines/start_screen.py` (`python -m ba.bot start_screen`). It ends on the lobby, or returns False on a popup for the lobby routine to close.
- Each cold start grows BlueStacks' memory by ~4–5 GB (9.2 GB after a restart, 22.8 GB after three launches). At 55 GB, with 0.2 GB left free on the PC, the load after TOUCH TO START stalled into the network-unstable popup and the bot's own capture ran out of memory. Restart BlueStacks before a long session.

## lobby (`ba/templates/start-screen/lobby/`)

The home screen: player level top left, AP, credits and pyroxene top centre, shortcuts on the left (Notice, MomoTalk, Attendance, Tasks, Cash Shop), the bottom bar (Cafe to Recruit) and Campaign bottom right.

- Identified by Campaign (`info_lobby_campaign_1728-996-156-46.png`) alone. It scores 1.00 under both popups below too, because neither covers it, so popups are checked before trusting it (Rule 1).
- Not seen yet: whether the HUD hides when idle, and what Back does here (a quit prompt?). `BACK_KEY` is still the scaffold's Android Back, untested on a menu.
- Automated by `ba/routines/lobby.py` (`python -m ba.bot lobby`). After a load or a popup close it watches 4 s more before counting the lobby as reached, since news shows ~2 s after Campaign. Run from the news popup, it closed news and reached the lobby. On later launches, news closed with no new-products after it.
- Tested after a BlueStacks restart: two cold starts (`start start_screen`, then `lobby`) each ended in the lobby, 37 s and 34 s after launch; and `python -m ba.bot start lobby` alone waited out the launch (the "Now Loading" template also matches the launch loads), handed over at the start screen, closed news and reached the lobby 32 s after launch. Not tested yet: from a menu a few taps deep, and the first launch of a new day with its popups.

## cafe (`ba/templates/start-screen/lobby/cafe/`)

Reached from the lobby's Cafe button. A "Tip!" loading screen (black with a gameplay tip) shows for 1–2 s on the way in. The room with visiting students; top: Back, "Cafe", AP/credits/pyroxene, settings, Home; Move to Cafe No. 2 and "Until Next Visit" timer under it; left: Planned Visit, Unannounced Visit; bottom: Edit, Gifts, Furniture, Presets, Store All, Bonus Invitation, Invitation, Comfort, Cafe Earnings.

- Identified by the "Cafe" title (`info_cafe_title_158-14-92-46.png`), and by the identifier of whichever dialog below is open. The title scores 1.00 under the reward popup too, so popups are checked first (Rule 1).
- Home (`btn_cafe_lobby_1830-12-54-46.png`, top right) goes straight to the lobby, no load. The lobby's Cafe dot went red → orange once earnings were claimed and the invite used.
- Only Cafe No. 1 (the one the cafe opens on) is mapped; Move to Cafe No. 2 isn't.
- Automated by `ba/routines/cafe.py` (`python -m ba.bot cafe`): claim earnings, invite the top-ranked student, Home. Tested only with nothing to claim and the invitation on cooldown (both skipped, back in the lobby in 19 s); the claim and invite paths are the steps mapped by hand, not yet run by the routine.

The dialogs below are states of the cafe (`screen-<state>.png`), each closed by its own button, not common popups.

### guide (`screen-guide.png`)

"Guide" / "Visiting Student List" with the visiting students' portraits, Confirm and X. Showed over the cafe on the first entry after launch; not on a later entry the same session.

- Identified by "Visiting Student List" (`info_cafe_guide-title_820-360-282-46.png`): at most 0.26 elsewhere. It can show after the "Cafe" title already matches, so the routine watches 3 s for it.
- Closed by Confirm (`btn_cafe_guide-confirm_792-636-338-104.png`).

### earnings (`screen-earnings.png`, `screen-claimed.png`)

Opened by Cafe Earnings bottom right (`btn_cafe_earnings_1668-950-196-36.png`, just the label: the full panel's crop included "100.0 %" and stopped matching at 0.0 %). Three panels (No. 1 credits, No. 1 AP, No. 2 credits) with earnings per hour and status, a Claim button and X.

- Identified by "Cafe Earnings" (`info_cafe_earnings-title_806-196-310-54.png`): at most 0.25 elsewhere.
- Claim (`btn_cafe_earnings-claim_796-742-330-100.png`) opens the reward popup. Afterwards the dialog stays open with the counters at 0 and Claim grey (`screen-claimed.png`). The template still scores 0.86 on grey Claim, so the routine tells them apart by colour: mean red minus blue over the button is +165 yellow, 0 grey.
- Closed by the X (`btn_cafe_earnings-close_1446-194-56-56.png`).
- A full claim gave 570,000 credits and 530 AP (No. 1 and No. 2 credits together).

### invitation (`screen-invitation.png`)

Opened by the Invitation ticket (`btn_cafe_invitation_1270-940-112-98.png`). A MomoTalk panel listing every student with heart level and an Invite button. Once used, the ticket turns grey with a ~20 h cooldown in its bubble, and the template no longer matches at all: that is how the routine skips it.

- Identified by the tips line "Only two students can be invited per Cafe at a time." (`info_cafe_invitation-tip_708-920-598-40.png`): at most 0.29 elsewhere. Not by the MomoTalk header, which the lobby's MomoTalk likely shares.
- Sorted by Name by default. The sort button (`btn_cafe_invitation-sort_998-200-186-56.png`) opens the sort state below; after sorting by Relationship Rank it reads so (`info_cafe_sort-by-relationship_1008-212-166-36.png`), and the order arrow flipped to descending on its own (highest rank first). Not seen yet: whether the sort persists to the next visit, and whether the direction can come up ascending.
- Invite on the first row (`btn_cafe_invite-first_1050-302-212-68.png`) opens invite-confirm. Not seen yet: what the first row shows when that student is already in the cafe.

### invitation-sort (`screen-invitation-sort.png`)

"Sort" panel over the list: Name, Academy, Relationship Rank, Pinned, and Confirm.

- Identified by "Sort" (`info_cafe_sort-title_636-294-72-40.png`): at most 0.28 elsewhere.
- Relationship Rank (`btn_cafe_sort-relationship_642-446-308-66.png`) turns pink when selected (`info_cafe_sort-relationship-selected_...`); Confirm (`btn_cafe_sort-confirm_640-562-632-60.png`) applies it and closes the panel.

### invite-confirm (`screen-invite-confirm.png`)

"Notice" / "<name> will be invited to the cafe." with Cancel and Confirm.

- Identified by "Notice" (`info_cafe_invite-notice_884-220-150-56.png`), which also matches network-unstable's title (1.00): trusted only after the common popups are checked. The message line is centred, so it moves with the name's length.
- Confirm (`btn_cafe_invite-confirm_972-706-354-100.png`) plays a MomoTalk "Inviting..." animation (~3 s), then the plain cafe shows with the student in the room.

## campus (`ba/templates/start-screen/lobby/campus/`)

Reached from the lobby's Lesson button (`btn_lobby_campus_276-1014-84-36.png`, the label), after a short load. The in-game title is "Lesson"; named campus here. Left: Tickets Owned N/6, Exp toggle, a guide character. Right: "Location Select" with Total Area Rank, Ticket Info, and a list of areas (Rank N, name, REWARD).

- Identified by "Location Select" (`info_campus_title_984-140-334-54.png`): at most 0.51 elsewhere. Not by the "Lesson" title.
- The area list scrolls on entry: a capture right after the load had Millennium Study Center on top, the settled list Schale Office. A tap on the top row while it scrolls may open another area.
- The top row (`btn_campus_location_980-228-716-146.png`, Schale Office's art) opens that area's map. The routine taps it as a point, (1338, 283), since which area it is doesn't matter.
- The lobby's Lesson dot disappeared once all tickets were spent.

## location (`ba/templates/start-screen/lobby/campus/location/`)

An area's map, "Select Location": rooms with the portraits of students there, an area-rank panel (Schale Office: Rank 8, 400 → 1000/2700 after six lessons), arrows to switch areas, All Locations bottom right. Locked rooms are grey with "Rank N required".

- Identified by the "Select Location" title (`info_location_title_158-12-300-50.png`), and by the identifier of whichever dialog below is open. The title still matches under them, so they are checked first.
- Home (`btn_location_lobby_1830-12-54-46.png`) goes to the lobby after a short load.
- Automated by `ba/routines/lesson.py` (`python -m ba.bot lesson`): one lesson per room card, in grid order, until no tickets are left, then Home. Tested with 0 tickets: lobby to All Locations and back in 27 s, nothing spent. The lesson path is the six lessons done by hand, not yet run by the routine.

The dialogs below are states of location (`screen-<state>.png`), not common popups.

### all-locations (`screen-all-locations.png`)

Opened by All Locations (`btn_location_all-locations_1630-970-240-54.png`). A grid of the area's rooms, 3 per row: Lv., name, the students there (a green check on each who earned relationship points today). Locked rooms are dark with "Rank N required" (Schale Office: Hangar, row 3). "Tickets Owned N/6" in its header.

- Identified by "All Locations" (`info_location_all-locations-title_810-126-300-52.png`): at most 0.30 elsewhere.
- Closed by the X (`btn_location_all-locations-close_1684-130-46-46.png`), back to the map.
- Ticket count: a crop of the whole "Tickets Owned N/6" line scored 0.94+ on every count from 6 to 0. Just the first digit (`info_location_tickets-zero_1040-210-22-34.png`) scores 1.00 on 0, 0.84 on 6, 0.74 on 5 and lower on 4-1, so the routine counts it as 0 only at 0.95 or more.
- Schale Office had 6 tickets and 6 unlocked rooms. Each room gave a lesson; the room's card doesn't change after one, so it can be picked again.
- Not seen yet: what tapping a locked card does. The routine taps it once and skips it if Location Info doesn't open.

### location-info (`screen-location-info.png`)

Opened by tapping a room card. Room, students, Lesson Rewards, a Tips line and Start Lesson with a ticket bubble (6 → 5).

- Identified by "Location Info" (`info_location_location-info-title_806-148-310-52.png`): at most 0.40 elsewhere.
- Start Lesson (`btn_location_start-lesson_816-800-290-54.png`) spends a ticket. A short animation, then zero or more relationship-rank-up popups, then lesson-report. Mission toasts ("Hold a lesson N time(s)") can slide over the top meanwhile.
- Closed by its X, around (1446, 173). Not tapped yet.

### lesson-report (`screen-lesson-report.png`)

Lesson Location, Relationship Points (students who earned them, a BONUS tag on some; "No Relationship Points earned." when no student there is recruited, as in Laboratory) and Lesson Reward (100 EXP plus an item or two).

- Identified by "Lesson Report" (`info_location_lesson-report-title_816-184-290-52.png`): at most 0.39 elsewhere.
- Confirm (`btn_location_report-confirm_864-808-192-56.png`) goes back to all-locations with the ticket count one lower.

## campaign (`ba/templates/start-screen/lobby/campaign/`)

Reached from the lobby's Campaign button (`btn_lobby_campaign_1728-996-156-46.png`, the label; it's also the lobby's identifier), with no load. Top row: Mission (with the current area and mission under it), Virtual Aptitude Test (locked, "Coming Soon..."), Story. Left column: Bounty, Commissions, Scrimmage. Right grid: Total Assault, Joint Firing Drill, Grand Assault, Tactical Challenge, Final Restriction Release. A guide character and an event banner on the left change between visits.

- Identified by the "Campaign" title (`info_campaign_title_158-12-206-50.png`): at most 0.47 elsewhere.
- Buttons are cropped to their title text only: the yellow dots, "In Progress" tags and subtitles (Mission's area and mission) come and go. Each scores at most 0.54 elsewhere.
- Every menu below has the same back arrow (`btn_<menu>_campaign_40-12-92-88.png`), which goes back to Campaign. The same arrow sits on the cafe, campus and location screens (0.98+), so it identifies nothing. Tactical Challenge's back arrow wasn't tapped yet.
- Not mapped yet: Story, Total Assault, Joint Firing Drill, Grand Assault, Final Restriction Release.

Each menu below is identified by its header at the top left (left of the "?" icon), at most 0.60 on any other saved screen.

### mission (`campaign/mission/`)

Header "Mission" (`info_mission_title_158-12-156-50.png`). Shows the current area (Area 20, 20th Mission): its art, Star Acquisition, Clear Reward, Multi-Sweep, and the stages on the right under Normal/Hard tabs (Hard showed, its stages locked).

### bounty (`campaign/bounty/`)

Header "Bounty" (`info_bounty_title_158-12-148-50.png`). Tickets Owned (21/6 when mapped) and a Location Select list: Overpass, Desert Railroad, Classroom. A 3x rewards event was running ("In Progress" tags on each area).

### commissions (`campaign/commissions/`)

Header "Commissions" (`info_commissions_title_158-12-270-50.png`). Request Select: Base Defense (student EXP items) and Item Retrieval (credits).

### scrimmage (`campaign/scrimmage/`)

Header "Scrimmage" (`info_scrimmage_title_158-12-230-50.png`). Tickets Owned (7/6 when mapped) and Academy Select: Trinity, Gehenna, Millennium. A 3x rewards event was running too.

### tactical-challenge (`campaign/tactical-challenge/`)

Header "Tactical Challenge" (`info_tactical-challenge_title_158-12-372-50.png`). The PvP screen. Left: player card, rank, Time Reward and Daily Reward with Claim buttons (both grey when mapped), Tickets Owned (5/5), Battle History, Defense Formation. Right: the season's three opponents (rank, team, level, name), Time Left and Refresh List.

## relationship-rank-up popup (`ba/templates/common/popups/relationship-rank-up/`)

Full-screen student art with a heart rank, "Relationship rank up!" and the stat gained (ATK +11, Healing +4, ...). Seen after lessons: one per student who ranked up (two in a row after Theater Room, none after Gym). It stays until tapped.

- Identified by its title (`info_relationship-rank-up_title_596-898-730-74.png`): at most 0.31 elsewhere.
- Closed by tapping the same title (`btn_relationship-rank-up_close_596-898-730-74.png`); the next rank-up or the lesson report follows.

## reward popup (`ba/templates/common/popups/reward/`)

"REWARD ACQUIRED!" with the items received and "TOUCH TO CONTINUE" at the bottom. Seen after the cafe earnings Claim; likely the same screen for other claims.

- Identified by "REWARD ACQUIRED!" (`info_reward_reward-acquired_556-200-590-78.png`, cropped short of the sparkle on its right end): at most 0.07 elsewhere.
- Closed by tapping "TOUCH TO CONTINUE" (`btn_reward_close_740-925-440-46.png`, centre (960, 948)): at most 0.19 elsewhere. It went back to the dialog it was opened from.

## news popup (`ba/templates/common/popups/news/`)

The news panel over the dimmed lobby: a sidebar of icons on the left, banners, and a "Main News" list. Showed on every launch so far (four on one day, not only the first), ~2 s after Campaign: a lobby seen right after the load isn't popup-free yet.

- Identified by "Main News" (`info_news_main-news-title_128-660-140-38.png`): 1.00 on the popup, at most 0.30 elsewhere.
- Closed by the X top right (`btn_news_close_1822-32-64-64.png`, centre (1853, 67)): at most 0.18 elsewhere. Closing it showed new-products.

## new-products popup (`ba/templates/common/popups/new-products/`)

"Notice" / "New products added." with paid packs, Confirm and Shortcut. Showed right after news closed.

- Identified by "New products added." (`info_new-products_message_768-670-384-50.png`): 1.00 on the popup, at most 0.21 elsewhere.
- Closed by the X top right (`btn_new-products_close_1380-120-50-50.png`, centre (1405, 144)): at most 0.22 elsewhere. Never tap Shortcut: it leads to a shop.

## network-unstable popup (`ba/templates/common/popups/network-unstable/`)

"Notice" / "The network connection is unstable. Tap the Confirm button to return to the title screen." with Confirm and Reconnect, over a dimmed loading screen. Seen during the load after TOUCH TO START, while the PC had 0.2 GB of memory free and BlueStacks used 55 GB, so it's likely memory pressure rather than the network. Cut by hand from the error screen, not via `tools.map`.

- Identified by its first line (`info_network-unstable_message_636-430-644-48.png`): 1.00 on the popup, no match on any other saved screen.
- Closed by Confirm (`btn_network-unstable_close_600-708-345-100.png`), which goes back to the start screen, where the routines carry on. Reconnect would retry the load. Not tapped yet. Its image also scores 0.98 on new-products' Confirm, but searched over the whole screen: that button sits outside this box.
- Android Back on the popup also seemed to leave it (black, a load, then the start screen).
