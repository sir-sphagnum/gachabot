# Blue Archive UI notes

How Blue Archive menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `ba/templates/` (see the map skill for the scheme). `ba/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `ba/`. Patterns Blue Archive shares with other games are in `core/notes/UI.md`, cited here as "(common: <section>)".

## start-screen (`ba/templates/start-screen/`)

The title screen: a movie of animated scenes under the Blue Archive logo, the copyright line at the bottom and the account's UID, version and region top right; once ready, "TOUCH TO START" in a bar at the bottom centre and Notice and Menu buttons bottom left. The movie plays without the buttons for a while: after a launch's loads, and after network-unstable's Confirm sent the game back to it (2026-11-22). Back on it opens a "Notice" dialog, probably a quit prompt (not captured).

- Identified by the copyright line (`info_start-screen_copyright_536-1028-850-32.png`), with or without the buttons: its letters are dark with a light outline, so the template is alpha-masked to the letters plus a 2 px outline (white-only matching failed over the bright floor of one scene). 1.00 on the scene it was cut from, 0.90 on the other scene seen, no match on the login transitions, at most 0.20 elsewhere. The 0.90 is close to the threshold: recut it if a new scene scores lower. The UID corner is never cut.
- START can be tapped once Notice (`info_start-screen_notice_42-862-116-52.png`) and Menu (`info_start-screen_menu_42-930-110-54.png`) show (the spec's `ready`): 1.00 on the start screen, at most 0.15 elsewhere. Until then the lobby routine waits, never pressing Back there. Not "TOUCH TO START", which pulses.
- Tapping the TOUCH TO START spot (`btn_start-screen_lobby_795-918-330-42.png`, centre (959, 940)) starts the game: 1.00 on its source, at most 0.31 elsewhere. As a match it's unreliable because of the pulse; tap it as a point.
- After the tap, "Now Loading . . ." screens show before the lobby: full-screen art that changes from load to load, with "Now Loading . . ." and a rabbit icon bottom right. `ba/templates/common/loading/info_loading_now-loading_1388-968-292-52.png` is the words without the animated dots, alpha-masked to the pixels that were the same on two loads with different art (42% of the box): 0.96 and 1.00 on those two, no match on any other saved screen. Art not seen yet may need it remasked (common: Loading screens).
- Launch to start screen took ~20 s on four cold starts; start screen to lobby 8–23 s.
- Passed by the lobby routine (`ba/routines/lobby.py`, `python -m ba.bot lobby`), which taps TOUCH TO START as a point.
- Each cold start grows BlueStacks' memory by ~4–5 GB (9.2 GB after a restart, 22.8 GB after three launches), so restart it before a long session (common: BlueStacks memory). At 55 GB the load after TOUCH TO START stalled into the network-unstable popup. During the daily routines it grew 0.6–7 GB per routine (lesson: 9.2 → 15.9 GB), and at 23.9 GB lesson stopped on blank screenshots. `ba.bot` runs each routine through `core.device.with_room`, which restarts BlueStacks before a routine when it's over 18 GB, and reruns the routine after a restart when it stops on blank screenshots or ADB stops answering anyway.

## lobby (`ba/templates/start-screen/lobby/`)

The home screen: player level top left, AP, credits and pyroxene top centre, shortcuts on the left (Notice, MomoTalk, Attendance, Tasks, Cash Shop), the bottom bar (Cafe to Recruit) and Campaign bottom right.

- Identified by Campaign (`info_lobby_campaign_1728-996-156-46.png`) alone. It scores 1.00 under both popups below too, because neither covers it, so popups are checked before trusting it (Rule 1).
- The HUD hides when the lobby sits idle (within a few minutes; the delay wasn't timed): the art alone shows, zoomed in (`screen-rest.png`), and Campaign stops matching. Back does nothing there (10 presses, still idle; common: Back). A tap on the art at (1500, 600) brings the HUD back.
- The idle lobby is identified by the hanging sign top right (`info_lobby_rest-sign_1530-90-320-370.png`): 1.00 on three idle captures, at most 0.47 elsewhere (0.47 on the lobby with its HUD up, whose framing differs). It is one of the lobby's identifiers, so `where` names an idle lobby as the lobby; the lobby routine wakes it (the spec's `idle`) before anything taps the HUD. One tap on the art woke it. Only this lobby art is known: another memorial lobby would need its own image.
- Back on the lobby with its HUD up shows nothing, but afterwards the game ignored every tap (Campaign, Cafe; ten `tap_until` taps over two minutes) until a second Back, after which Campaign opened at the first tap. Seen once, 2026-11-22.
- The Tasks shortcut (`btn_lobby_tasks_44-378-62-30.png`, the label without its N/8 badge) opens tasks, with no load: at most 0.60 elsewhere.
- Automated by `ba/routines/lobby.py` (`python -m ba.bot lobby`), a `core.lobby` spec. Its `settle` is 4 s, since news shows ~2 s after Campaign. On later launches, news closed with no new-products after it. The "Now Loading" template also matches the launch loads, so they're waited out as loads. Cold starts reached the lobby 32–37 s after launch.
- Run live as a `core.lobby` spec on 2026-11-22: a cold start after a BlueStacks restart (title movie waited out, one TOUCH TO START tap, login-board closed by its sky tap, transitions waited out, idle lobby woken, news caught by the hold; ~65 s), and from overpass (three Backs, 11 s).
- The first launch of a day shows, after TOUCH TO START and before the lobby, a banner and then one login board after another (2026-11-16: live-stream banner, Daily Attendance, 5-Year Anniversary, Back to Work), then a dark fade into the idle lobby. On 2026-11-22 the fade was a dark hall, then the lobby's art in grey, then a white flash, ~15 s in all after the board; nothing in them is mapped, so the lobby loop waits them out inside its window after START. A login board also showed on later launches that day. Back on them only toasts "Unavailable right now." (common: Back). Both are common popups (banner, login-board below), so the lobby loop closes them like news. They're popups, not lobby states, because they show before the lobby is drawn (common: First of the day or week). On 2026-11-22 the lobby loop closed a login board with one or two sky taps; the banner wasn't seen.

## tasks (`ba/templates/start-screen/lobby/tasks/`)

The daily missions (common: Daily missions). Reached from the lobby's Tasks shortcut, no load. Tabs All, Daily, Weekly, Achievement, Challenges (red dots on the ones with rewards waiting); a list of task rows, each with a reward and a yellow Claim or a blue Shortcut; a bottom bar with the "Complete at least 8 Daily Task(s)" milestone (N/8, its own Claim) and Claim All. Home (`btn_tasks_lobby_1830-12-54-46.png`) goes to the lobby with no load; once it was ignored and a second tap took.

- Identified by the "Tasks" title (`info_tasks_title_158-14-116-48.png`): at most 0.22 on every other capture. It scores 1.00 under the mailbox and reward popups, so popups are checked first (Rule 1).
- Opens on the All tab, which lists the daily rows with the others, so no tab is picked.
- Claim All (`btn_tasks_claim-all_1570-962-312-88.png`) claims the ready rows but not the milestone. Its claim can complete "Complete at least 5 Daily Task(s)", which lights Claim All again, so it was tapped twice. Grey Claim All scores 0.84 on the template, so colour decides (common: Lit or grey): mean red minus blue over it is +168 yellow, −2 grey.
- First Claim All opened the mailbox popup, then the reward popup; the second went straight to the reward popup.
- The milestone Claim (`btn_tasks_milestone-claim_1388-962-146-84.png`) paid 20 pyroxene at once, with no popup (common: Reward dialogs), and turned grey "Complete": +164 yellow, −8 grey.
- When Claim All completes the 8th task, the milestone's Claim lights a moment after the reward popup closes: a look right after the close saw it grey while it was ready (2026-11-21).
- Automated by `ba/routines/claim_dailies.py` (`python -m ba.bot claim_dailies`): Claim All while yellow, then up to 5 s for the milestone to light, then the milestone while yellow, then Home. Run once (2026-11-21): Claim All claimed, but the milestone was taken as grey before the wait was added, and was claimed by hand. The wait hasn't run yet.

## mail (`ba/templates/start-screen/lobby/mail/`)

The Mailbox, opened by the envelope in the lobby's top-right bar (`btn_lobby_mail_1700-28-64-52.png`, cut without its red dot: 1.00 on the lobby, 0.99 on the news popup's capture, which has the lobby under it). Tabs Unclaimed, Product, Receipt History on the left (opens on Unclaimed); the mails on the right, each with its own Claim; a "N/200" count; Claim All bottom right ("Up to 100 items can be claimed at once"). Home (`btn_mail_lobby_1830-12-54-46.png`) goes to the lobby with no load.

- Identified by the "Mailbox" title (`info_mail_title_160-12-160-50.png`): at most 0.54 elsewhere. It still matches under the reward popup.
- Claim All (`btn_mail_claim-all_1550-965-305-80.png`) is yellow while anything is unclaimed and grey once the mailbox is empty; grey still scores 0.89 on it, so colour decides (common: Lit or grey): mean red minus blue over it is +164 yellow, −1 to −3 grey. With 6 mails, one tap claimed all of them and opened the reward popup; closing it left "No more mail." (`info_mail_empty_1010-715-280-50.png`), 0/200 and a grey Claim All.
- Automated by `ba/routines/claim_mail.py` (`python -m ba.bot claim_mail`): Claim All while yellow (popups closed between taps), then Home. Run with nothing to claim (lobby to lobby in 5 s); the claim path was done by hand while mapping, on 2026-11-18.

## cafe (`ba/templates/start-screen/lobby/cafe/`)

Reached from the lobby's Cafe button. A "Tip!" loading screen (black with a gameplay tip) shows for 1–2 s on the way in. The room with visiting students; top: Back, "Cafe", AP/credits/pyroxene, settings, Home; Move to Cafe No. 2 and "Until Next Visit" timer under it; left: Planned Visit, Unannounced Visit; bottom: Edit, Gifts, Furniture, Presets, Store All, Bonus Invitation, Invitation, Comfort, Cafe Earnings.

- Identified by the "Cafe" title (`info_cafe_title_158-14-92-46.png`), and by the identifier of whichever dialog below is open. The title scores 1.00 under the reward popup too, so popups are checked first (Rule 1).
- Home (`btn_cafe_lobby_1830-12-54-46.png`, top right) goes straight to the lobby, no load. The lobby's Cafe dot went red → orange once earnings were claimed and the invite used.
- Only Cafe No. 1 (the one the cafe opens on) is mapped; Move to Cafe No. 2 isn't.
- Automated by `ba/routines/cafe.py` (`python -m ba.bot cafe`): claim earnings, invite the top-ranked student, Home. Tested with nothing to claim and the invitation on cooldown (both skipped, back in the lobby in 19 s), and with both ready: the claim worked. The invite skips students visiting Cafe No. 2 (invite-neighbor below); that path hasn't run yet: the ticket was on cooldown once it was written.

The dialogs below are states of the cafe (`screen-<state>.png`), each closed by its own button, not common popups.

### guide (`screen-guide.png`)

"Guide" / "Visiting Student List" with the visiting students' portraits, Confirm and X. Showed over the cafe on the first entry after launch; not on a later entry the same session.

- Identified by "Visiting Student List" (`info_cafe_guide-title_820-360-282-46.png`): at most 0.26 elsewhere. It can show after the "Cafe" title already matches, so the routine watches 3 s for it.
- Closed by Confirm (`btn_cafe_guide-confirm_792-636-338-104.png`).

### earnings (`screen-earnings.png`, `screen-claimed.png`)

Opened by Cafe Earnings bottom right (`btn_cafe_earnings_1668-950-196-36.png`, just the label: the full panel's crop included "100.0 %" and stopped matching at 0.0 %). Three panels (No. 1 credits, No. 1 AP, No. 2 credits) with earnings per hour and status, a Claim button and X.

- Identified by "Cafe Earnings" (`info_cafe_earnings-title_806-196-310-54.png`): at most 0.25 elsewhere.
- Claim (`btn_cafe_earnings-claim_796-742-330-100.png`) opens the reward popup. Afterwards the dialog stays open with the counters at 0 and Claim grey (`screen-claimed.png`). The template still scores 0.86 on grey Claim, so the routine tells them apart by colour (common: Lit or grey): mean red minus blue over the button is +165 yellow, 0 grey.
- Closed by the X (`btn_cafe_earnings-close_1446-194-56-56.png`).
- A full claim gave 570,000 credits and 530 AP (No. 1 and No. 2 credits together).
- **earnings-full** (`screen-earnings-full.png`): with AP at its cap (999/208), Claim opened "Notice" / "Insufficient inventory space. Make space to proceed." with the AP icon, Confirm and an X, and claimed nothing. Identified by its message (`info_cafe_earnings-full-message_700-584-520-50.png`: at most 0.33 elsewhere); it covers the earnings title. Confirm (`btn_cafe_earnings-full-confirm_780-745-360-100.png`, the shared Notice button: 0.63 on best-record's) closes it; where it leads hasn't been seen, since the images were cut from an error screen. Below the cap the claim went through, the AP past the cap going to the mailbox (mailbox popup), so the daily order spends AP (`sweep_hard`) before `cafe`.

### invitation (`screen-invitation.png`)

Opened by the Invitation ticket (`btn_cafe_invitation_1270-940-112-98.png`). A MomoTalk panel listing every student with heart level and an Invite button. Once used, the ticket turns grey with a ~20 h cooldown in its bubble, and the template no longer matches at all: that is how the routine skips it.

- Identified by the tips line "Only two students can be invited per Cafe at a time." (`info_cafe_invitation-tip_708-920-598-40.png`): at most 0.29 elsewhere. Not by the MomoTalk header, which the lobby's MomoTalk likely shares.
- Sorted by Name by default. The sort button (`btn_cafe_invitation-sort_998-200-186-56.png`) opens the sort state below; after sorting by Relationship Rank it reads so (`info_cafe_sort-by-relationship_1008-212-166-36.png`), and the order arrow flipped to descending on its own (highest rank first). Not seen yet: whether the sort persists to the next visit (common: Settings that stick), and whether the direction can come up ascending.
- Five rows show in full, 117 px apart: Invite centres at x 1156, y 336 / 453 / 570 / 687 / 804 (`btn_cafe_invite-first_1050-302-212-68.png` is the first). The rows look the same whether or not the student is in a cafe, so the routine taps them as points, top down: invite-confirm means the student can come; invite-neighbor means they're visiting Cafe No. 2, so Cancel and try the next row. Not seen yet: what a row does when the student is already in Cafe No. 1; the routine moves on when a row opens neither dialog.

### invite-neighbor (`screen-invite-neighbor.png`, `screen-invite-neighbor-move.png`)

"Invite Neighboring Student" in two steps, both with Cancel, Confirm and an X: first "Invite a student visiting the Neighboring Cafe. If you invite a student, there will be an empty spot in that cafe. Proceed?"; then the student's portrait "No. 2 → No. 1" (`screen-invite-neighbor-move.png`). Confirming both (done by hand once) moved the student to Cafe No. 1 and put the ticket on cooldown, with no "Inviting..." animation.

- Identified by its title (`info_cafe_invite-neighbor-title_736-230-448-52.png`): 1.00 on the first step, 0.95 on the second (it sits 7 px lower), at most 0.44 elsewhere.
- Cancel (`btn_cafe_invite-neighbor-cancel_600-712-340-92.png`) is the shared Confirm/Cancel art, 1.00 on invite-confirm and sweep-confirm, so it's tapped only while the title shows (common: Shared buttons).

### invitation-sort (`screen-invitation-sort.png`)

"Sort" panel over the list: Name, Academy, Relationship Rank, Pinned, and Confirm.

- Identified by "Sort" (`info_cafe_sort-title_636-294-72-40.png`): at most 0.28 elsewhere.
- Relationship Rank (`btn_cafe_sort-relationship_642-446-308-66.png`) turns pink when selected (`info_cafe_sort-relationship-selected_...`); Confirm (`btn_cafe_sort-confirm_640-562-632-60.png`) applies it and closes the panel.

### invite-confirm (`screen-invite-confirm.png`)

"Notice" / "<name> will be invited to the cafe." with Cancel and Confirm.

- Identified by its message without the name, "will be invited to the cafe." (`info_cafe_invite-text_798-478-420-50_anywhere.png`): 1.00 here, at most 0.37 elsewhere. The line is centred, so it moves with the name's length, and it's searched anywhere. Not by its "Notice" title, which every Notice dialog shares (common: Shared buttons): it made the lobby loop read the quit dialog as the cafe.
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
- Automated by `ba/routines/lesson.py` (`python -m ba.bot lesson`): one lesson per room card, in grid order, until no tickets are left, then Home. Tested with 0 tickets (lobby to All Locations and back in 27 s, nothing spent) and with 6: six lessons, a rank-up popup closed on the way, lobby to lobby in 60 s.

The dialogs below are states of location (`screen-<state>.png`), not common popups.

### all-locations (`screen-all-locations.png`)

Opened by All Locations (`btn_location_all-locations_1630-970-240-54.png`). A grid of the area's rooms, 3 per row: Lv., name, the students there (a green check on each who earned relationship points today). Locked rooms are dark with "Rank N required" (Schale Office: Hangar, row 3). "Tickets Owned N/6" in its header.

- Identified by "All Locations" (`info_location_all-locations-title_810-126-300-52.png`): at most 0.30 elsewhere.
- Closed by the X (`btn_location_all-locations-close_1684-130-46-46.png`), back to the map.
- Ticket count: a crop of the whole "Tickets Owned N/6" line scored 0.94+ on every count from 6 to 0. Just the first digit (`info_location_tickets-zero_1040-210-22-34.png`) scores 1.00 on 0, 0.84 on 6, 0.74 on 5 and lower on 4-1, so the routine counts it as 0 only at 0.95 or more (common: Reading a zero).
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
- Buttons are cropped to their title text only, without the yellow dots, "In Progress" tags and subtitles (common: Moving parts). Each scores at most 0.54 elsewhere.
- Every menu below has the same back arrow (`btn_<menu>_campaign_40-12-92-88.png`), which goes back to Campaign. The same arrow sits on the cafe, campus and location screens (0.98+), so it identifies nothing (common: Shared buttons). Tactical Challenge's back arrow wasn't tapped yet.
- Not mapped yet: Story, Total Assault, Joint Firing Drill, Grand Assault, Final Restriction Release.

Each menu below is identified by its header at the top left (left of the "?" icon), at most 0.60 on any other saved screen.

### mission (`campaign/mission/`)

Header "Mission" (`info_mission_title_158-12-156-50.png`). Shows the current area (Area 20, 20th Mission): its art, Star Acquisition, Clear Reward, Multi-Sweep, and the stages on the right under Normal/Hard tabs (Hard showed, its stages locked). Home (`btn_mission_lobby_1830-12-54-46.png`) goes to the lobby after a short load.

- Multi-Sweep (`btn_mission_multi-sweep_712-860-182-44.png`) looks the same whether or not today's sweeps are used: open it to find out.
- Mission toasts ("Use 7000 AP", "Obtain 30 equipment blueprint(s)") slide over the top centre after a sweep, covering dialog titles there, so the dialogs below are identified lower down (common: Toasts).
- Automated by `ba/routines/sweep_hard.py` (`python -m ba.bot sweep_hard`): sweep the preset Multi-Sweep opens on, MAX times, then Home. Tested with the sweeps used up (Mission to lobby in 24 s, nothing spent) and with them ready: swept, lobby to lobby in 2.5 min, most of it waiting on Sweep Complete. Not seen yet: what shows when AP is short.

The dialogs below are states of mission (`screen-<state>.png`), not common popups.

#### multi-sweep (`screen-multi-sweep.png`, `screen-multi-sweep-done.png`)

Preset tabs 1–7 and an edit pencil; a Selection List of stages (preset 1: Hard 14-2, 17-2, 18-3 and more below, each ticked, with Remaining Count N/3 and drops); Filter, sort, Undo all selections; Register Target (three student pieces), MIN / − / count / + / MAX, Save, and a yellow Multi-Sweep button with an AP bubble (964 → 904 at count 1).

- Identified by "Selection List" (`info_mission_selection-list_166-324-186-44.png`): 1.00 on all three captures of it, at most 0.33 elsewhere. Not by the "Multi-Sweep" title, which a toast covered (0.67).
- MAX (`btn_mission_sweep-max_1174-856-108-64.png`) set the count 1 → 3, the daily limit; MAX and + then go grey, − orange; the bubble read 964 → 784.
- The Multi-Sweep button (`btn_mission_sweep-start_1546-862-246-50.png`) opens sweep-content. Once every ticked stage is used up (`screen-multi-sweep-done.png`: rows dimmed "Used all remaining counts.", count 0, bubble 784 → 784) it turns grey, and its template still scores 0.91 there. The routine tells them apart by colour: mean red minus blue over the button is +139 yellow, −2 grey.
- Closed by the X (`btn_mission_multi-sweep-close_1808-126-50-50.png`).

#### sweep-content (`screen-sweep-content.png`)

"Sweep Content" / "Use 180 AP to sweep the stages below." with the selected stages and their Sweep Count, Cancel, Confirm and X.

- Identified by its title (`info_mission_sweep-content-title_784-126-352-56.png`): at most 0.42 elsewhere.
- Confirm (`btn_mission_sweep-confirm_980-832-344-94.png`) spends the AP; Sweep Complete showed ~2 s later.

#### sweep-complete (`screen-sweep-complete.png`)

"Sweep Complete": player EXP gained (+450, Bonus +180), a scrolling list of rewards per sweep, "Final Rewards Earned", Confirm and X.

- Identified by "Final Rewards Earned" (`info_mission_sweep-complete-final_304-686-234-82.png`): at most 0.41 elsewhere. The title sits under the toasts.
- Confirm (`btn_mission_complete-confirm_784-820-354-110.png`) goes back to multi-sweep, now in its done state.

### bounty (`campaign/bounty/`)

Header "Bounty" (`info_bounty_title_158-12-148-50.png`). Tickets Owned (21/6 when mapped) and a Location Select list: Overpass, Desert Railroad, Classroom. A 3x rewards event was running ("In Progress" tags on each area). The ticket count is shared by all three areas.

- Overpass (`btn_bounty_overpass_1624-250-204-50.png`, the name only) opens overpass with no load. Desert Railroad and Classroom aren't mapped yet.

#### overpass (`campaign/bounty/overpass/`)

"Bounty - Overpass" panel on the left: Bounty Ticket N/6, the event line, Academy Buff. Right: Stage List, one row per stage (number, stars, name, Enter). The top-left header still reads "Bounty" (common: Shared titles). Home (`btn_overpass_lobby_1830-12-54-46.png`) goes to the lobby after a short load.

- Identified by "Bounty - Overpass" (`info_overpass_title_162-218-418-56.png`): at most 0.36 elsewhere.
- The Stage List scrolls to its last stages on entry (common: Lists that move): 06–10 show, 05 is cut off at the top. Enter centres sit at x 1676, y 357 / 506 / 655 / 805 / 954. Enter looks the same on every row (`btn_overpass_stage-enter_...` is row 09's).
- Stars tell cleared stages apart: mean red minus blue over a row's stars (x 1042–1116, 10–38 px below its Enter) is +62 gold, −5 grey. When mapped, 06–09 had 3 gold stars and 10 (Overpass J) grey.
- Ticket count: just the first digit (`info_overpass_tickets-zero_414-278-24-36.png`) scores 1.00 on 0 and 0.42 on 21. Other counts weren't seen, so the routine counts 0 only at 0.95 or more.
- Automated by `ba/routines/bounty.py` (`python -m ba.bot bounty`): sweep the lowest gold-starred row MAX times (every ticket), then Home. Tested with 0 tickets (lobby to Overpass and back in 18 s, nothing spent) and with tickets: swept, lobby to lobby in 27 s. If a new stage is 3-starred lower in the list, the picker follows it on its own. A list longer than five visible rows below 05 wasn't seen.

The dialogs below are states of overpass (`screen-<state>.png`), not common popups. Scrimmage's gehenna opens the same three, and uses these images (common: Shared screens).

##### mission-info (`screen-mission-info.png`, `screen-mission-info-done.png`)

Opened by a row's Enter. Stage number and name, Rec. level, Mission Objectives, Expected Rewards; a Sweep panel (Min / − / count / + / Max, Start Sweep with a ticket bubble 21 → 20) and Start Mission (also 1 ticket).

- Identified by "Mission Info" (`info_overpass_mission-info-title_824-186-274-52.png`): at most 0.41 elsewhere.
- Max (`btn_overpass_sweep-max_1568-420-108-64.png`) set the count 1 → 21, every ticket (bubble 21 → 0); Max and + go grey, − orange.
- Start Sweep (`btn_overpass_sweep-start_1272-586-266-50.png`) opens sweep-confirm. With 0 tickets (`screen-mission-info-done.png`: count 0, bubbles "0 → -") Start Sweep and Max still look lit.
- Closed by the X (`btn_overpass_mission-info-close_1664-184-54-54.png`).

##### sweep-confirm (`screen-sweep-confirm.png`)

"Notice" / "Use N Bounty Ticket to Sweep N time(s)?" with Cancel, Confirm and X.

- Confirm (`btn_overpass_sweep-confirm_976-708-348-100.png`) spends the tickets. It's the same button as the cafe's invite-confirm (1.00), so it's trusted only right after Start Sweep (common: Shared buttons).

##### sweep-complete (`screen-sweep-complete.png`)

"Sweep Complete": player EXP bar, the rewards of each sweep listing one at a time with a Skip button under them, then "21 time(s) Rewards Earned", "Final Rewards Earned" and Confirm. Mission toasts ("Clear a Bounty 20 time(s)", "Complete at least 8 Daily Task(s)") slide over its title meanwhile. The same dialog as mission's sweep-complete: its images score 1.00 on each other's screens.

- Identified by "Final Rewards Earned" (`info_overpass_sweep-complete-final_302-682-238-86.png`), which shows only once the list is done (a few seconds for 21 sweeps; Skip wasn't tapped).
- Confirm (`btn_overpass_sweep-done_788-822-346-106.png`) goes back to mission-info with the count at 0.

### commissions (`campaign/commissions/`)

Header "Commissions" (`info_commissions_title_158-12-270-50.png`). Request Select: Base Defense (student EXP items) and Item Retrieval (credits).

### scrimmage (`campaign/scrimmage/`)

Header "Scrimmage" (`info_scrimmage_title_158-12-230-50.png`). Tickets Owned (7/6 when mapped) and Academy Select: Trinity, Gehenna, Millennium. A 3x rewards event was running too. The ticket count is shared by all three academies.

- The header stays on every academy's screen below (1.00 on gehenna), so an academy is identified by its own panel title, never by the header (common: Shared titles).
- Gehenna (`btn_scrimmage_gehenna_1624-410-204-54.png`, the name only) opens gehenna with no load: at most 0.54 elsewhere. Trinity and Millennium aren't mapped yet.

#### gehenna (`campaign/scrimmage/gehenna/`)

Panel on the left: "Gehenna", Tickets Owned N/6, the event line, art. Right: Stage List, four rows (01 Gehenna A to 04 Gehenna D; 03 and 04 locked when mapped). The list doesn't scroll. Home (`btn_gehenna_lobby_1830-12-54-46.png`) goes to the lobby after a short load.

- Identified by "Gehenna" (`info_gehenna_title_162-220-202-54.png`): at most 0.47 elsewhere.
- Rows share overpass's layout: Enter at x 1676, y 279 / 429 / 578 / 728, stars 10–38 px below Enter. Stars read +64 on 01 (3 gold), −2 to +6 on 02–04 (grey, locked). `btn_gehenna_stage-enter_...` is row 01's Enter.
- Ticket count: just the first digit (`info_gehenna_tickets-zero_430-278-20-36.png`) scores 1.00 on 0 and 0.46 on 7 (common: Reading a zero).
- Enter opens the same Mission Info, Notice and Sweep Complete as overpass, in the same places: overpass's images score 1.00 on gehenna's captures, so gehenna has no copies and its routine uses overpass's (common: Shared screens). Each sweep costs 1 ticket and 10 AP; the Notice reads "Use Scrimmage Ticket N, AP 10N to Sweep N time(s)?". 7 sweeps of 01 gave 9 + 21 keys and 189K credits at the 3x event.
- Automated by `ba/routines/scrimmage.py` (`python -m ba.bot scrimmage`): sweep the lowest gold-starred row MAX times, then Home. The sweep steps are shared with bounty (`ba/routines/stage_sweep.py`). Tested with 0 tickets (from the idle lobby to Gehenna and back in 16 s, nothing spent) and with tickets: swept, lobby to lobby in 27 s.

### tactical-challenge (`campaign/tactical-challenge/`)

Header "Tactical Challenge", cut to "Tactical Challen" (`info_tactical-challenge_title_158-12-312-50.png`): mission toasts start at x ≈ 478 and covered the full word ("Complete at least 8 Daily Task(s)": 0.84 on the full crop, 1.00 on this one; at most 0.42 elsewhere) (common: Toasts). The PvP screen. Left: player card, rank, Time Reward (+N/minute, Total N/1,000K) and Daily Reward with Claim buttons, Tickets Owned N/5, Standby Time, Battle History, Defense Formation. Right: the season's three opponents (rank, team, level, name), Time Left and Refresh List. Home (`btn_tactical-challenge_lobby_1830-12-54-46.png`) goes to the lobby after a short load.

- The opponent rows are sorted by rank, best at the top. The list refreshes after every fight, won or lost, so the top row is a new opponent each time. Its strength varies a lot: in one list the top row was a Lv.89 player with a Lv.82 team (a loss), in the others Lv.23–27 players with Lv.17–26 teams (wins). The top row is tapped as a point, (1268, 375): its crop holds the portrait, rank and team, and matched only its source (at most 0.76 elsewhere).
- Ticket count: just the first digit (`info_tactical-challenge_tickets-zero_326-716-20-36.png`) scores 1.00 on 0 and 0.51–0.73 on 5, 4, 3 and 1 (common: Reading a zero).
- Standby Time stayed "--:--" through five fights in a row: no wait between fights.
- Claim buttons (`btn_tactical-challenge_time-reward-claim_...`, `btn_tactical-challenge_daily-reward-claim_...`) score 0.81 on their grey state, so colour decides (common: Lit or grey): mean red minus blue over each is +167 yellow, −2 grey. Both turned yellow after the first win. Each opens the common reward popup: Time Reward gave 220 credits (Total back to 0), Daily Reward 12 pyroxene and 40 Tactical Challenge Coins, after which it shows a countdown (11:04).
- Each win raised the rank to the beaten opponent's and paid pyroxene on a new best (80, 60, 60, 60); rank 4890 turned the rank icon gold.
- Automated by `ba/routines/tactical_challenge.py` (`python -m ba.bot tactical_challenge`): fight the top row until the ticket count reads 0, skipping each battle, then claim both rewards while yellow, then Home. Tested with 0 tickets (from the idle lobby, it claimed the Time Reward built up since the last claim, skipped the grey Daily Reward and was back in the lobby in 20 s) and with 3: three wins (~30 s each, best-record closed after each), both rewards claimed, lobby to lobby in 2.5 min. The loss path hasn't run yet.
- best-record left open blocks `core.nav.goto`'s walk to the lobby: Back on it only toasts "Unavailable right now." (common: Back). The routine closes it after each fight, so this happens only when a run stopped between a fight and that close.

The dialogs below are states of tactical-challenge (`screen-<state>.png`), not common popups.

#### battle-opponent (`screen-battle-opponent.png`)

Opened by tapping an opponent row. "Battle Opponent" with a Time Left countdown, Opponent Info VS My Info, X, and Attack Formation with a ticket bubble (5 → 4).

- Identified by its title (`info_tactical-challenge_battle-opponent-title_776-118-372-56.png`): at most 0.49 elsewhere.
- Attack Formation (`btn_tactical-challenge_attack-formation_800-812-326-88.png`) opens attack-formation. The ticket is spent by the fight, not by opening the formation.

#### best-record (`screen-best-record.png`)

"Best Season Record Reached!" with the new and old rank and a pyroxene reward, over tactical-challenge right after a win that set a new best rank. The pyroxene is already added when it shows.

- Identified by its title (`info_tactical-challenge_best-record-title_634-208-652-56.png`): at most 0.36 elsewhere. The menu's header matches under it, so it is checked first (Rule 1).
- Closed by Confirm (`btn_tactical-challenge_best-record-confirm_800-764-328-96.png`).

#### attack-formation (`campaign/tactical-challenge/attack-formation/`)

Header "Attack Formation" (`info_attack-formation_title_158-12-400-50.png`, at most 0.52 elsewhere). Unit 1's four strikers and two specials, Quick Formation, Starting Skill, Unit Info, Presets, a Skip Battle checkbox (unticked, not tried) and Mobilize. Reached only through battle-opponent, so `core.nav goto attack-formation` can't open it on its own.

- Mobilize (`btn_attack-formation_mobilize_1640-976-220-62.png`) starts the battle: an intro cutscene, then the battle HUD 6–9 s after the tap. The battle runs on AUTO (locked on) with a 3:00 limit.
- » top right of the HUD (`btn_attack-formation_battle-skip_1812-34-80-70.png`) skips the rest of the battle: the HUD goes at once and the result shows ~2 s later. It slides in over the first seconds (0.99 while sliding), so it is located on the live screen before each tap. Not the cyan ▶▶ bottom right, which is the battle speed.

The screens below are states of attack-formation (`screen-<state>.png`).

- battle-result (`screen-battle-result.png`): "Battle Complete" with the team and Confirm (`btn_attack-formation_battle-confirm_1656-952-196-88.png`, at most 0.46 elsewhere). The STRIKER label (`info_attack-formation_battle-result-striker_60-862-136-40.png`) matches here and under the reward screen.
- battle-reward (`screen-battle-reward.png`): "REWARD ACQUIRED!" (1000 credits) over the result, with a yellow Confirm at the bottom centre ~1 s later (`btn_attack-formation_reward-confirm_800-940-324-96.png`). Its title scores 0.96 as the common reward popup's, whose close spot is this Confirm, so the routine doesn't check popups between the result and tactical-challenge. Confirm goes back to tactical-challenge.
- lose (`screen-lose.png`): "LOSE" (`info_attack-formation_battle-lose_726-424-468-160.png`, at most 0.20 elsewhere) and a yellow Confirm (`btn_attack-formation_lose-confirm_788-936-348-104.png`), which opens lose-tip.
- lose-tip (`screen-lose-tip.png`): "Tip!" (`info_attack-formation_lose-tip_444-132-156-76.png`) with an upgrade tip and the same bottom Confirm as battle-reward (0.99), which goes back to tactical-challenge.

## relationship-rank-up popup (`ba/templates/common/popups/relationship-rank-up/`)

Full-screen student art with a heart rank, "Relationship rank up!" and the stat gained (ATK +11, Healing +4, ...). Seen after lessons: one per student who ranked up (two in a row after Theater Room, none after Gym). It stays until tapped.

- Identified by its title (`info_relationship-rank-up_title_596-898-730-74.png`): at most 0.31 elsewhere.
- Closed by tapping the same title (`btn_relationship-rank-up_close_596-898-730-74.png`; common: Tap anywhere); the next rank-up or the lesson report follows.

## area-rank-up popup (`ba/templates/common/popups/area-rank-up/`)

"AREA RANK UP!" over a white band with the area's new rank badge ("Rank 9"), "New zone unlocked!" and "TOUCH TO CONTINUE". Seen once, over all-locations after a lesson raised the area's rank (2026-11-21); after a tap, the lesson report showed. A common popup because it shows after whichever lesson crosses a rank, and then lesson's taps close it.

- Identified by "AREA RANK UP!" (`info_area-rank-up_title_548-205-822-110.png`): at most 0.24 elsewhere.
- Closed by tapping the same title (`btn_area-rank-up_close_548-205-822-110.png`; common: Tap anywhere). Cut from the error screen: by hand, a tap on TOUCH TO CONTINUE moved on; the title tap hasn't run yet.

## reward popup (`ba/templates/common/popups/reward/`)

"REWARD ACQUIRED!" with the items received and "TOUCH TO CONTINUE" at the bottom. Seen after the cafe earnings, mail, tasks and Tactical Challenge claims (common: Reward dialogs).

- Identified by "REWARD ACQUIRED!" (`info_reward_reward-acquired_556-200-590-78.png`, cropped short of the sparkle on its right end): at most 0.07 elsewhere.
- Closed by tapping "TOUCH TO CONTINUE" (`btn_reward_close_740-925-440-46.png`, centre (960, 948)): at most 0.19 elsewhere. It went back to the dialog it was opened from.

## mailbox popup (`ba/templates/common/popups/mailbox/`)

"Notice" / "The acquired item will be sent to your mailbox as you have reached the ownership limit. Please check your mailbox." with Confirm and an X, over the reward popup. Seen after tasks' Claim All, the first one only; likely after any claim of an item at its limit.

- Identified by its first line (`info_mailbox_message_624-404-668-50.png`): at most 0.25 elsewhere. Not by "Notice", which several dialogs share (common: Shared buttons).
- Closed by Confirm (`btn_mailbox_close_780-706-358-102.png`): at most 0.25 elsewhere. The reward popup shows under it.

## news popup (`ba/templates/common/popups/news/`)

The news panel over the dimmed lobby: a sidebar of icons on the left, banners, and a "Main News" list. Showed on every launch so far (four on one day, not only the first), ~2 s after Campaign: a lobby seen right after the load isn't popup-free yet.

- Identified by "Main News" (`info_news_main-news-title_128-660-140-38.png`): 1.00 on the popup, at most 0.30 elsewhere.
- Closed by the X top right (`btn_news_close_1822-32-64-64.png`, centre (1853, 67)): at most 0.18 elsewhere. Closing it showed new-products.

## new-products popup (`ba/templates/common/popups/new-products/`)

"Notice" / "New products added." with paid packs, Confirm and Shortcut. Showed right after news closed.

- Identified by "New products added." (`info_new-products_message_768-670-384-50.png`): 1.00 on the popup, at most 0.21 elsewhere.
- Closed by the X top right (`btn_new-products_close_1380-120-50-50.png`, centre (1405, 144)): at most 0.22 elsewhere. Never tap Shortcut: it leads to a shop.

## network-unstable popup (`ba/templates/common/popups/network-unstable/`)

"Notice" / "The network connection is unstable. Tap the Confirm button to return to the title screen." with Confirm and Reconnect, over a dimmed loading screen. Seen during the load after TOUCH TO START: once with BlueStacks at 55 GB and 0.2 GB free on the PC, once (2026-11-22) at ~10 GB, so memory pressure isn't its only cause. Cut by hand from the error screen, not via `tools.map`.

- Identified by its first line (`info_network-unstable_message_636-430-644-48.png`): 1.00 on the popup, no match on any other saved screen.
- Closed by Confirm (`btn_network-unstable_close_600-708-345-100.png`), which goes back to the start screen, where the routines carry on: on 2026-11-22 the lobby loop's Confirm tap led back to the title movie. Reconnect would retry the load. Its image also scores 0.98 on new-products' Confirm, but searched over the whole screen: that button sits outside this box.
- Android Back on the popup also seemed to leave it (black, a load, then the start screen).

## login-board popup (`ba/templates/common/popups/login-board/`)

A full-screen login reward board: Arona on the left in a classroom over water, a board on the right whose title, cards and size change by event (`screen.png` Daily Attendance, `screen-anniversary.png`, `screen-back-to-work.png`). It waits for a tap before the next board or the lobby.

- Identified by the classroom's sky and windows top left (`info_login-board_sky_0-0-640-120.png`), the one part no board covers and Arona doesn't move through: 1.00 on all three boards, at most 0.56 on every other saved screen. So a new event's board needs no new image, as long as it keeps the classroom.
- Closed by a tap on that same sky (`btn_login-board_close_...`, centre (320, 60)). Not tried there yet: by hand, a tap on today's card, on another day's card and on the empty space under the board each moved on, so a tap anywhere seems to (common: Tap anywhere).

## banner popup (`ba/templates/common/popups/banner/`)

A full-screen event banner (art changes per event) with "Don't show again today" bottom left and an X top right. Showed first on the new day's launch.

- Identified by "Don't show again today" (`info_banner_dont-show_40-1002-320-48_white.png`), and closed by the X (`btn_banner_close_1818-16-72-72_white.png`): both over the art, so both are matched white-only. 1.00 on the banner, at most 0.29 elsewhere. news's X is a different image (0.17 on the banner's).
