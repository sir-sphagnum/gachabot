# Arknights UI notes

How Arknights menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `ak/templates/` (see the map skill for the scheme). `ak/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `ak/`. Patterns Arknights shares with other games are in `core/notes/UI.md`, cited here as "(common: <section>)".

Android Back closes menus (`BACK_KEY = "back"`); on the lobby it opens quit.

## Launch

Launch → launch load → pre-start → title (`start-screen`) → Connecting → Rhodes Island load → lobby. A cold start took 45 s from launch to the lobby with no login popups; pre-start showed 11–30 s after launch (longer on the first launch of the day, which checks for updates).

- **Launch load:** lore art (rotating "Victorian Empire", "Originium"…) under a "Clear Cache" button, with a status line ("Loading network configuration…", "Checking resource integrity…"). It has no template: "Clear Cache" and the art show on pre-start too, so an image of them would read pre-start as a load and `past_loading` would wait on it. The lobby spec's `launch` wait (90 s) covers it instead (common: Loading screens).
- **Connecting** (`common/loading/connecting/`): "Connecting to the neural network of Rhodes Island." under a spinning wireframe, ~6 s after START. Text 1.00 on its frames, not found on the lobby or the Rhodes Island load.
- **Download** (`common/loading/download/`): "Releasing neurotransmitter (n MB/m MB)" over the launch art, with a % bar along the bottom, then "Decompressing files. No traffic data will be consumed…" over the same bar. Each cut on its first words only and searched `_anywhere`: the line is centred, so it moves as the MB count changes length. ~5 MB/s: a hotfix of 330 MB took about a minute, the 13 GB basic package ~45 minutes, far past `core.nav.past_loading`'s wait.
- **resource-error** (stop screen, `common/stops/resource-error/`): "Error occurred during the resource completeness check. Please tap on Confirm to re-download the missing files." with a round tick, over the launch art while "Checking resource integrity" runs. Seen on 2026-11-22 before resource-package (below), for the same reason and the user's call for the same reason. Identified by its first words, white-only over the art (150, 482), at most 0.24 elsewhere.
- **resource-package** (stop screen, `common/stops/resource-package/`): "Download the complete resource package (13631.69MB)" or "the basic resource package (13330.21MB)", with Quit and Confirm. Shown when the game's data is incomplete: on 2026-11-22, after `core.device restart` closed BlueStacks twice during a launch update. Which package, and whether to download at all, is the user's call (they chose basic), and the lobby loop presses Back on screens it doesn't know, which it did here three times. So it's a stop screen: the lobby loop gives up on it untouched, and `core.device` doesn't restart over it (`stuck_on`). Identified by the complete package's line without its size (684, 392), at most 0.48 elsewhere.
- **voice-settings / voice-settings-ticked** (popups): "Use JP voices / Use EN voices / Keep current settings", Confirm grey until one is ticked, over pre-start after its diamond is tapped. Seen after the data loss above. Two popups, since a popup has one close: unticked (the "Keep current settings" line and its empty box) is closed by ticking that box, which keeps the user's voices; ticked (the box with its tick) by Confirm (786, 696). The empty and ticked boxes score 0.44 on each other, so neither reads as the other. It opens over pre-start, which still matches under it (pre-start, below).
- **login-notice** (popup): a "Facebook Login Notice" over the title, closed by Understood (876, 800); title at most 0.38 elsewhere. The logo still matches under it, so unmapped it reads as the title without START, which the lobby loop waits on (as a game logging in) instead of closing. Back also closes it.
- **voice-pack** (popup): "Download JP voice pack / EN / CN – Mandarin / KR / personalized", installed ones ticked and grey. Its close is Confirm (786, 870) with the ticks left as they are, which adds no pack; a 330 MB download followed, the launch update or the installed packs' files, not told apart. Identified by its "Download JP voice pack" line (668, 80), at most 0.30 elsewhere.
- **Rhodes Island load** (`common/loading/rhodes/`): the Rhodes Island emblem over a blurred scene and a tip line, ~4 s. Cut on the emblem's "RHODES ISLAND" (1.00 on its frames, not found on Connecting or the lobby). Probably the load between menus too: not checked yet.

## pre-start (popup)

The launch load's last screen: the same lore art with a yellow START diamond at the bottom. A popup, not a menu, so the lobby routine closes it like any other (`common/popups/pre-start/`): `info_` and close are both the diamond (914, 976, 92×92), at most 0.15 elsewhere. A tap takes it to the title within ~10 s, or opens a launch dialog over it (voice settings). The diamond sits in the black bar below the art, outside a dialog's dim, so it still matches under one, pulsing around the 0.85 threshold: one look sees it, the next misses it. A dialog over pre-start therefore reads as pre-start, and taps on the diamond land on the dialog. So the lobby spec checks pre-start after every other popup (`last`). A dialog not mapped yet can't be told from pre-start: the diamond's close fails (`core.nav.close_popup` counts it closed only once it stays gone), the routine gives up with the dialog in its error screen, and `core.device` doesn't restart over it (`stuck_on`).

## start-screen

The title: ARKNIGHTS logo, grey START, side buttons (support, notice, …, refresh) and the account ID bottom right (personal: never in a crop or note). Identified by the logo (520, 380, 870×150), at most 0.19 elsewhere; START (806, 716, 308×102) at most 0.19. START goes at the tap; the logo stays ~1 s, then Connecting, the Rhodes Island load, and the lobby ~12 s after the tap.

## lobby

Identified by the Squads tile (1050, 465, 185×80), at most 0.19 elsewhere; the "Sanity /173" label (1160, 350, 160×45) at most 0.22. The HUD stays up (the eye button at (374, 605) hides it by hand only), so nothing needs waking.

- **Sanity** is the stamina (common: Stamina sink, `core/notes/dailies.md`): the big number on the Terminal tile, top right of the HUD, over "Sanity /<max>". Max 173 at account level 13; it rises with the level, so the label's max isn't fixed either.
- **Login popups** (first launch of the day, common: First of the day or week): the lobby shows clear ~1 s, then in turn checkin with resource-today over it, events-board, event-login. Closing one opens the next, and each closes by its own button (below).
- Reached by `ak/routines/lobby.py`, a `core.lobby` spec. On 2026-11-22: a cold start in 51 s (launch load waited out, pre-start closed, one START tap, no Back pressed), from base through its leave dialog in 14 s, and from the quit dialog.
- **quit** (state): Back on the lobby opens "Are you sure you want to exit?" (735, 465, 450×48, at most 0.24 elsewhere), over a blur that hides Squads. Closed by its X (630, 706, 72×72); the red tick quits.
- Other HUD entries seen: settings, notices, mail (envelope, (254, 28)), calendar, Terminal (stages), Squads, Operator, Store, Recruit, Headhunt, Missions (orange badge with the count to claim), Base (badges for emergencies and notifications), Depot, Friends, Archives, and the current event's "Limited Sign-In" banner under the settings gear.

## mail

The envelope at the top left of the lobby (254, 28, 76×58; at most 0.57 elsewhere). Identified by the line "Mail will be deleted starting from the oldest…" (60, 1020, 790×40), at most 0.15 elsewhere. Rows have Check and Collect (grey once collected); Collect All bottom right (1546, 952), Delete Read next to it. Collect All stays blue with nothing left, and then answers with a "No mail to claim" toast at the top right (1572, 160) for a few seconds (common: Toasts); with attachments it opens resource-gained.

## Popups

All in `common/popups/`. The reward and sign-in screens drift particles over their buttons, so a click on them is `--moving`.

- **resource-today:** "Resource Today" title over the sign-in calendar's daily item, closed by the round tick (916, 916). Title at most 0.69 elsewhere (on resource-gained, the same layout).
- **resource-gained:** "Resource Gained", the reward dialog after a claim (common: Reward dialogs), same layout and tick. Title at most 0.67 elsewhere.
- **checkin:** the monthly sign-in calendar; the day is signed in on open. Identified by its "Daily Supply" tag (1260, 198), at most 0.42 elsewhere; closed by the X (1782, 62).
- **events-board:** Cumulative Sign-In / Rookie Mission / Consecutive Sign-in tabs; rewards are given on open. Identified by the Rhodes Island art in the left column's foot (60, 560, 290×420), at most 0.14 elsewhere; closed by the X (1828, 70).
- **event-login:** the current event's login board (now "Hunting Time", ends 2026/11/30). Identified by its title art, which goes with the event, so a new event's board is a new popup to map. The day's card must be tapped to claim it (Resource Gained follows); the X (1808, 112) closes it without claiming.

## missions

The lobby's Missions tile (1072, 830). Opens on Pinboard (newbie phases), or on another tab with rewards waiting; identified by Pinboard's tab label (832, 28, at most 0.28 elsewhere), which shows on every tab. The Daily tab reads chosen when dark (`info_missions_daily-chosen`), light grey when not: the two score 0.09–0.14 on each other.

- Daily: a "Collect All" banner tops the list while any row is finished (`btn_missions_collect-all`, under 0.5 on every other screen); one tap claims every finished row and opens resource-gained. Claimed rows sink to the bottom as "All Collected".
- Once all ten reward sets are claimed the tab greys out under a large "CLAIMED" stamp, with the rows still listed (seen 2026-11-22, the day's goal).
- Rows and the reward sets: `ak/notes/dailies.md`. The list scrolls (a swipe 1240,900 → 1240,200 moves about four rows).

## base

The lobby's Base tile (1384, 845), through the "Rhodes Island Infrastructure Complex" load (`common/loading/base/`). Identified by the "Building Mode" toggle label (36, 290).

- **Notification bar:** the bell (1764, 182) opens a bar along the bottom: Backlog, then Collectable "n Collect All", Orders Acquired "n Exchange All", Trust "n Collect All", Rotate, Clues. A claim leaves the bar at once (a toast says what it gave, no dialog) and the entries after it shift left into its slot, so the labels are cut `_anywhere` and searched along the bar's strip only: Trust's label scored 0.94 on the "Trust increased" toast. A tap outside the bar closes it.
- **leave** (state): Back on the base opens "Leave the Base?", and Back again cancels it, so a Back loop toggles it for ever. The lobby routine answers it with the tick (1232, 712), which goes to the lobby; the tick is the quit dialog's art (1.00 there), so only the leave text identifies it.
- **dormitory:** tapping the Dormitory tile opens Dormitory B104: Operator panel (left column) lists the residents with morale; Assign opens dorm-assign, an operator grid sorted by Morale, with "on shift" on those working elsewhere, Confirm bottom right.

## credit-store

Store's Credit Store tab (1652, 130), identified by its own tab label. "Claim" next to the credit count (1460, 46) is orange (red − blue 180) while the day's credit waits and grey "Collected" (0) after (common: Lit or grey); a claim opens resource-gained (+46 credit on 2026-11-22). The items cost credit; nothing here buys them.

## friends

Lobby's Friends tile (440, 820); Friends list tab at (28, 276). Identified by its "My Info" header (1126, 48). The account has no friends, so the "Visit friends' Bases" row can't be done.

## terminal / main-theme

Terminal (lobby tile at (1356, 200)) holds the main theme tile (810, 150); main-theme is the stage map. It opens on the newest stage (2-3) with that stage's panel open, which hides the episode switcher (bottom right); a tap on empty map (640, 960) closes the panel. The switcher's left button reads the previous episode ("EPISODE 01" on Episode 02, crop only matching there); its middle reads the current one.

- A stage's panel shows its title, stars, Enemy Info, Rewards, the Auto Deploy toggle, Practice and Start with the Sanity cost. Auto Deploy unlocks on a 3-star clear made **without** a support unit (S2-4's padlock, cleared with support, says so); 1-11 is a fixed-squad stage with no Auto Deploy. Ticked, it shows a repeat counter "×1" to its left, which is how the routine reads it on (common: Settings that stick); it stays on between runs.
- Episode 01 at its right end (six swipes from its start) shows 1-10, 1-11, 1-12. 1-12 "Pyrrhic Victory": leader W, 30 enemies, 9 Sanity. 2-1 "To Lungmen" (Episode 02's left end): no leader, 50 enemies, 9 Sanity.
- **squad:** after Start, the recorded roster with "The roster for this operation cannot be changed" (its identifier); MISSION START (1554, 550) starts the fight.
- **The fight** plays itself under Auto Deploy; the speed toggle (1636, 72) flips 1X/2X and stays on 2X between fights. A run took ~2.5 min at 2X.
- **stage-result:** "OPERATION COMPLETE / MISSION RESULTS" with stars and drops; a tap goes through the Rhodes Island load back to the stage map, the stage still picked.
- **level-up** (popup): "Level Up" with the Sanity restored and the new max, in place of the result on the run that crosses a level (common: Level up). Tap anywhere; the title (466, 534) is its close.
