# Common UI notes

Menu behaviour that more than one game shows, and how the bot deals with it. Each game's `notes/UI.md` keeps what is specific to its menus (boxes, scores, which button, thresholds) and cites a section here as "(common: <section>)" instead of explaining it again. Every `<game>/CLAUDE.md` imports this file next to its own notes.

A pattern moves here once a second game shows it: one game alone can't tell a quirk of that game from a general one. How to cut images (`_anywhere`, `_white`, alpha masks) is in the map skill; this file says when a menu needs them. Rules the routines must follow are below (Rules), numbered and cited as "Rule N" across the project; how a lesson becomes one is in `.claude/doc_policy.md` §4.

## Rules

### Rule 1. Check for popups before trusting a state indicator

A popup or dialog that dims the screen leaves what's underneath matching, so an indicator showing is not proof the game is in that state. Before acting on an indicator match, check that none of the game's known popups, nor any dialog the current menu can have open, is open, and close any that is before looking again.

- `891ce78`: the quit dialog dims the lobby; the wall barrel still matched (0.96), so the routine took it for the lobby and tapped the candle, which did nothing.
- `8c73f0c`: the barrel matched through "Disconnected from server"; the routine handed over to `tap_until`, which closed the popup and kept tapping the main-menu spot on the start screen it led to.

**Scope:** this covers matches that decide what state the game is in. It doesn't cover a popup's or dialog's own `info_` images, or a wait whose result a popup-checking loop looks at again before acting.

### Rule 2. Judge a tap by the screen it settles on

A game answers a tap late, for a moment, or not at all: the result can show a second after the check, an element can drop out of one capture while it animates, and a tap during an animation is ignored. So one look right after a tap proves nothing. Tap with `core.nav.tap_until`, which watches for the result for `delay` seconds and taps again only once that time has passed (it takes a `check(screen)` as well as images). Wait for a late result with a deadline (`core.device.wait_until`), and when a result can flicker, require it to hold (`core.nav.held`).

- `4af7b1a`: after Buy the check looked once, still saw the 100-heart price (the card moves a moment after the dialog closes) and failed a buy that had gone through.
- `ada27e7`: START dropped out of one capture during its intro animation, so the routine took it as gone and waited 60 s for a lobby while the ignored tap left START on screen.

**Scope:** this covers taps whose result the routine checks. It doesn't cover a tap that spends something each time it lands (Cultivate, a Buy or Start confirm): that one is tapped once and waited on, never retapped.

### Rule 3. A check this file describes is written once, in core

When this file describes how to read the screen, the code for it lives once in `core/` and routines call it: `core.nav.clear` (popups closed before reading a menu, Rule 1), `core.vision.tint` (lit or grey), `core.vision.diff` (a counter or icon that changed between frames), `core.nav.settled` (a list that stopped moving), `core.nav.scroll_to` (an entry past the screen's edge), `core.nav.past_loading` (black and loading screens waited out), `core.nav.held` and `tap_until` (Rule 2). A routine that needs a check core lacks adds it to core.

- `7c56885`, `7670c5f`, `8ead727`, `e557780`: each routine that read a lit button wrote its own `_lit`, with a different slice order, channel unpacking and comparison, though the notes describe one rule.
- `7c56885`, `5efc4e3`, `7670c5f`, `8ead727`, `e557780`, `b94626e`, `9669062`: seven routines carried their own `_clear` for Rule 1, some closing one popup, some looping, some checking the title.

**Scope:** this covers how the screen is read and waited on. It doesn't cover a menu's own numbers (boxes, thresholds, offsets), which stay in the routine next to a comment on what was measured, nor a routine's sequence of steps.

### Rule 5. Identify a state by an element only it has

Games reuse art across screens, and an image cut from one scores ~1.00 on the others (Shared buttons, Shared screens, Shared titles, Reading a zero, below). So a menu, state or dialog is identified only by an element no other screen shows (a question line, a panel title, a card only that menu has), checked against every saved screen when it's cut. A shared image closes, confirms or taps, never identifies, and is tapped only once the state is known.

- `316053a`: a title chosen for arena turned out to be shared by the next menu, and the identifier had to be undone.
- `bacb050`: re1999's Home was noted as scoring at most 0.19 elsewhere; it scored 0.94–0.99 on every show screen, so each menu there got its own `info_`.

**Scope:** this covers images that decide which screen is shown. It doesn't cover a dim (Rule 1), where the matching element really is on screen, under the dialog.

### Rule 6. Judge a step by the state it was meant to reach

A step can reach its goal without the signal the routine expected on the way: no reward dialog, a confirmation title missed, a control already gone because its work is done. So a step is judged done by its goal state: the control that does the work gone, grey or showing a timer, the setting's indicator on. A missing control or dialog is read as done, not as failure, once the menu it belongs to is known (Rule 5) and has settled (Rule 2).

- `0170ea0`: claiming MolaGora Farm opens no reward dialog, so `tap_until` kept waiting for "Tap to close" and the routine gave up after the claim had gone through.
- `db9e34f`: claim_auto waited for Calculation Complete's title, missed it, and failed a claim that had gone through.
- `ed88516`: with three products bought, 5 Flags moved past the screen's edge, and claim_daily_shop failed it as "not on screen".
- `2d1b72a`: battle-prep remembered replay mode, so the play icon that turns it on was gone and the run failed looking for it.

**Scope:** this covers judging whether a step's work is done. It doesn't cover deciding which screen is open (Rules 1 and 5), and it never makes a spend retappable (Rule 2's scope).

## Dims

A popup or dialog dims the screen but leaves what's underneath matching (Rule 1), often at 0.96–1.00: e7's barrel under the quit dialog, re1999's Crew under quit, ba's Campaign and Cafe titles under their popups. A game's notes record only the score under the dim.

## Shared buttons

Games reuse one button's art across dialogs: e7's "Tap to close" sits on five dialogs and its quit-dialog Cancel/Confirm on three more; ba's Confirm is the same on the cafe's invite and bounty's sweep, and its "Notice" title heads several dialogs. The back arrow and Home sit in one spot on every menu (ba's top bar, re1999's Home at (186, 42), e7's back arrow). So (Rule 5) a shared `btn_` is tapped only right after the action that opens its dialog, or while that dialog's own `info_` (its question line, or a title nothing else shares) shows, and the back arrow and Home only once the menu is known.

## Shared screens

A menu can show another menu's screens unchanged: e7's secret-shop buy dialog is daily-shop's (title, Cancel and Buy all 1.00 there); ba's gehenna opens overpass's Mission Info, Notice and Sweep Complete in the same places, and mission's Sweep Complete is that dialog too; re1999's battle-prep-pneuma and battle-prep-poussiere are In Our Time's battle-prep, and all three fight on its battle screen.

- No copies are cut: the second menu's routine uses the first menu's images, and its notes say where they live. A copy would be a second image to keep in step for no new information.
- No `info_` is cut from a shared screen (Rule 5). The screen is told open by its control (e7's green Buy), and the menu by what differs (re1999's Pneuma chances line) or, where nothing does, by the path that reached it (re1999's poussiere).

## Shared titles

A menu one level down often keeps the title or header of the one above: e7's arena-landing and arena both read "Arena", battle and hunt both "Battle"; ba's "Bounty" header stays on overpass and "Scrimmage" on gehenna. So the title identifies neither (Rule 5); each is identified by an element only it has (e7's Arena card and Defense Team; ba's panel titles "Bounty - Overpass" and "Gehenna").

## Lit or grey

Matching ignores brightness, so a lit button and its greyed, claimed or used-up version score alike (0.86–0.98). Tell them apart by colour: the mean of one channel minus another over the button's box, red minus blue for yellow, orange, gold and red, green minus blue for green and blue. The threshold goes halfway between the lit and grey values the game's notes record. A dim pulls the value toward grey, so it's read only with dialogs closed. `core.vision.tint(screen, box, "r-b")` reads it; the routine keeps the box and threshold, with the values they came from.

Seen on e7's Cultivate, secret-shop's Buy, arena's Challenge and lost rows, orbis-guide's chest badge and the HUD badge; ba's cafe Claim, Multi-Sweep and bounty's stars; re1999's chosen Tasks tab (orange fill).

## Settings that stick

Menus remember a choice between visits and after fights: e7's Use Owned Energy First stays ticked; re1999's replay mode and its x4 count stay on, and battle-prep reopens in replay mode with the play icon gone. And a toggle often scores the same either way (re1999's Hard 1.00 / 0.99, its Daily tab label 1.00 / 0.90). So:

- the routine reads the setting from its own indicator (e7's ticked box, re1999's replay line and "x4" in the count box) before touching it, and taps the toggle only while the indicator says it's off: a blind tap can turn it off again;
- a control that turns a setting on can be gone because the setting is already on (re1999's play icon), so its absence is judged by the indicator (Rule 6).

## Daily missions

Every game is assumed to have a daily-missions menu, and each one gets a `claim_dailies` routine (`python -m <game>.bot claim_dailies`) that only claims and never works on the missions. So far: e7's orbis-guide (Three Sisters' Diary), re1999's tasks (Daily Activeness tab), ba's tasks (Claim All, then the milestone's own Claim).

- **One tap claims everything.** e7's 100 chest claims every ready chest on the bar; re1999's Claim All claims every finished task and milestone. The routine taps that one control, not each row, and taps it again while it's still lit: ba's Claim All can complete a "claim N tasks" task, which lights it again, and leaves the milestone on the bottom bar to its own Claim.
- **The claim control shows or lights only while something is claimable.** e7's chest badge is lit only then; re1999's Claim All banner is there only then. So "not there" or "not lit" means already claimed or not earned yet, which the routine counts as success (Rule 6).
- **A claim opens a reward dialog** (common: Reward dialogs): e7's is the menu's own state; re1999's and ba's are common popups.
- **The menu may open on another tab or section**, so the routine picks the daily one after every entry (re1999 opens on a tab with rewards waiting, Weekly once Daily is claimed).
- **A claimed row can come back as its next tier**: a harder row of the same kind (clear 1 stage → 8, defeat 100 enemies → 300 → 500, reach 50 activity → 100), counting the day's total so far. So the rows on a first visit can be fewer than the day holds, and the day's missions are done only once the menu's goal is claimed (its top chest, or every reward set), not once the rows first seen are.

## Reward dialogs

A claim (missions, mail, earnings, a fight's reward) usually opens a dialog listing what it gave, which waits for a tap. e7's are each menu's own state, closed by the shared "Tap to close" (common: Shared buttons); ba's "REWARD ACQUIRED!" and re1999's "Obtained" are common popups that can show over any menu.

- When it's one of the game's common popups, the claim tap runs with `popups=False`, or `tap_until` closes it as an obstruction and keeps tapping (re1999's claim_mail and claim_dailies).
- Some claims open none (e7's MolaGora Farm, ba's 8/8 milestone Claim), so a claim is judged by its control (Rule 6), not by a dialog showing.
- Another popup can sit on top of it (ba's mailbox notice at an ownership limit) and is closed first.

## Reading a zero

A counter is read as "zero or not" from a crop of its first digit only. Other digits score 0.42–0.84 against the 0 (rounded ones, 6, 8 and 9, come closest), so the routine asks for 0.90–0.95, not the usual 0.85. Counts that were never seen are unknown, so the notes list which were. Over a changing background the digit is matched white-only (`_white`). A bare digit can match a digit on another menu (e7: hunt-team's top bar scores 0.91 on arena's flags 0), so it's read only once the menu is known (Rule 5).

Seen on e7's arena flags and leif cost, ba's lesson and bounty tickets.

## Moving parts

- Text that pulses or has art moving across it is masked to its letters: re1999's START and loading line, ba's "Now Loading" (masked to the pixels two loads with different art shared).
- A pulsing button is tapped as a point rather than found by matching: ba's TOUCH TO START.
- Animated scenes never give two identical captures, so `tools.map` flags them "still changing" and settling is judged by a still element (a title, a list): e7's sanctuary and secret-shop.
- Crops keep the text and leave out what comes and goes: badges, orange dots, counts, sparkles, EVENT and "In Progress" tags, subtitles.

## Tap anywhere

Some screens have no close button and move on at a tap anywhere: re1999's obtained, level-up and VICTORY, ba's relationship-rank-up and login boards, e7's start screen. The routine taps the screen's identifier: the `btn_` is cut on the same box as its `info_` (re1999's obtained and level-up titles, ba's rank-up title, ba's login-board sky), so the tap lands only while the screen it closes shows. A spot on blurred background (re1999's checkin-close) marks a tap point only, never a state: its crop is background, which changes with what's behind it.

## Toasts

Chat and mission toasts slide over the top of the screen for a few seconds (e7's "entered channel" toast, ba's mission toasts over dialog titles). Identifiers are taken where toasts don't reach.

A toast can also be a tap's only answer: e7's "Receive All cannot be used with this mail." and re1999's "No mail with attachment" (nothing to claim), ba's "Unavailable right now." (Back refused), re1999's "Dust +7125" (collected). It's gone within seconds, so the routine looks for it in the tap's own wait (a `tap_until` check), not after.

## Lists that move

Lists scroll on entry or reorder: e7's hunt list scrolls to the chosen card and the daily-shop grid moves bought products to the end; ba's lesson area list and bounty stage list scroll on entry; re1999's resource row moves Pneuma Analysis to the end once its chances are spent. Entries are found with `_anywhere` images or tapped by position once the list has settled (`core.nav.settled`), never while it scrolls. A list that reorders can push an entry off screen: e7's daily-shop grid, with three products bought, puts 5 Flags past the right edge. `core.nav.goto` taps only what is on screen and never swipes, so it can't reach an entry past the edge: the entry is cut `_anywhere`, and the routine brings it on screen with `core.nav.scroll_to` (wait for the list to settle, look, swipe, wait again) and only then taps it.

Stage lists and timelines open on the newest or last stage (re1999's In Our Time and resource timelines, ba's overpass), which moves as the account progresses. So a stage is found by its label `_anywhere` (re1999) or picked by reading the rows (ba's stars), never at a fixed spot.

## Loading screens

Loads come between screens: e7's are black (`core.nav.past_black` waits them out); ba's "Now Loading" and re1999's launch loading screen show art that changes, so they're identified by their text masked to its letters (common: Moving parts) and kept in `<game>/templates/common/loading/`. ba's image also matches the launch loads.

- Nothing on a load answers Back, and a Back that lands as the load ends acts on what follows (re1999: Backs on the splash and the start screen's fade-in opened the quit dialog). So lobby routines wait while a load shows (`core.nav.loading` tells one, `core.nav.past_loading` waits past it and past black), and, for the first seconds after launch (`core.device.uptime`), on any screen they don't know.
- A load not mapped yet (re1999's story and wilderness loads, ba's cafe "Tip!") reads as an unknown screen, where the lobby routine presses Back once the launch wait is over. Map it when a routine trips on it.

## Back

Android Back doesn't close every screen. ba's idle lobby ignores it, ba's login boards and best-record only toast "Unavailable right now.", and e7's web-notice ignores it too. A lobby routine walking home by Back runs out of presses on them, and `core.nav.goto`'s walk to the lobby stops there. So each such screen is a common popup or a menu dialog with its own close (ba's best-record is closed by its routine after each fight, the idle lobby woken by a tap). On the lobby itself Back opens the quit dialog (Lobbies, below); on loads see Loading screens.

## Lobbies

- Back on the lobby opens a quit dialog (e7, re1999), so the lobby routine opens it whenever it presses Back once too often. It's closed with Cancel; Confirm quits the game.
- The lobby's HUD hides when idle (e7 after ~9 s, ba within minutes). The idle lobby needs an identifier from the scene (e7's barrel, ba's hanging sign), and the lobby routine wakes it before anything taps the HUD.
- Login dialogs are handled as First of the day or week (below) says.

## First of the day or week

Every game shows screens only on the first launch of a day, or the first entry of a menu in a day or week: e7's check-in dialogs (after the date change), its guild hall's dialog and arena's weekly rank reward; re1999's login reward, check-in card, event-login and profile panel; ba's banner and login boards. Mapping and testing happen on later launches, so these are missing from the templates, and a routine meets them first on the next day's run, where they stop it (`ffb80d0`, `8b62e7c`, `4575157`, `06f1cc9`).

- Where they're handled depends on what can be read underneath. A dialog over a lobby that is already identifiable is a lobby state (e7's check-in, re1999's checkin card). One that shows before the lobby is drawn, or over any menu, is a common popup, so start_screen and lobby close it (ba's boards, re1999's event-login). One that a single menu shows on entry is that menu's dialog, waited for on entry (e7's arena reward).
- Their art changes with events, so they're identified by what stays: ba's login boards by the classroom behind every board, not by a board's title.
- Back often does nothing on them (common: Back), so a lobby routine's Back presses don't get past them.

## BlueStacks memory

BlueStacks' memory grows with every capture and every cold start (e7: 9.6 → 22 GB in ~45 min of two processes capturing each second; ba: ~4–5 GB per cold start). Past ~22 GB screencaps came back empty; with 0.2 GB free on the PC, ba's load stalled into its network-unstable popup. `python -m core.device health` says when a restart is due. Claude then runs `python -m core.device restart <game>` without asking, at the next safe moment: no spend, fight, load or half-done claim in flight, and no fight or long recording started before it. Each `<game>.bot` runs its routines through `core.device.with_room`, which restarts BlueStacks (and the game, to its lobby) before a routine once it's over 18 GB, and once more, rerunning the routine, if it stops on blank screenshots or on ADB not answering (ba: `screencap` timed out at 19.5 GB, after a cold start took it past the limit mid-routine).
