# E7 UI notes

How E7 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `e7/templates/` (see the map skill for the scheme). Add new menu notes here, not as notes.md files in the template folders. `e7/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `e7/`.

## start-screen (`e7/templates/start-screen/`)

The title screen ("Tap to Start"). Its one indicator is also its button: the copyright line "© Smilegate. All Rights Reserved." at the bottom centre (`btn_start-screen_lobby_805-1023-311-26_white.png`). Tapping it, like tapping anywhere, starts the game and loads the lobby at rest.

- Launch: E7 opens in a floating window (black, copyright line at its bottom), then once fullscreen shows a black loading screen for ~2 s before the start screen. Tapping start gives another black load (~7 s) before the lobby at rest. Black screens are waited out (`core.nav.past_black`), never acted on.
- A Google Play Games welcome toast (dark pill, top centre) shows over the start screen for a few seconds. The copyright line still matches under it.
- Automated by `e7/routines/start_screen.py` (`python -m e7.bot start_screen`).

## lobby (`e7/templates/start-screen/lobby/`)

Five states: active and rest, each seen by day and by night, quit, checkin and checkin-received. The scene's lighting changes with the time of day: at night the tavern is warmer and brighter. `screen.png` is the night lobby, active (the usable state). `screen-day.png` is the day lobby, active. `screen-night.png` is the night lobby, at rest. `screen-rest.png` is the day lobby, at rest. `screen-quit.png` is the quit dialog over the lobby. `screen-checkin.png` and `screen-checkin-received.png` are the two daily check-in dialogs.

- **active**: HUD shown. Identified by the barrel **and** `btn_lobby_main-menu_1847-20-45-58.png` (blue 4-boxes, top right; also opens the main menu). Neither is enough alone: the barrel shows in every lobby state, and the 4-boxes icon also shows on other screens (e.g. the shop).
- **rest**: HUD hidden, only the animated tavern scene. Identified by `info_lobby_barrel_1240-140-80-120.png` (the big barrel on the wall right of the bar, centre ~(1280, 200)) while the 4-boxes icon is missing. The barrel is part of the scene, so it shows in every state and on `main-menu`. It's covered by some popups and absent on the shop and start screens.
- **quit**: "Are you sure you want to quit the game?" with Cancel (left, brown) and Confirm (right, blue), over the dimmed lobby. Escape in the lobby opens it, so the `lobby` routine opens it whenever it presses Back one time too many. It's a lobby state rather than a common popup because only the lobby opens it, and always on Escape.
  - Identified by its question (`info_lobby_quit-text_690-462-540-50.png`), matched in colour: 1.0 on the dialog, at most 0.45 elsewhere (the disconnected popup's message).
  - Closed by tapping Cancel (`btn_lobby_lobby_660-650-280-80.png`, back to the active lobby): 1.0 on the dialog, at most 0.29 elsewhere. Never tap Confirm: it quits the game.
  - Escape also closes it, but takes ~1.4 s to clear the text. Pressed again before that, it can land on the lobby and open the dialog again; a tap on Cancel can't.
  - The wall barrel still matches through the dim (0.96). The HUD icons don't.
- **checkin**: "Merurin's Check-In Reward", a 28-day calendar (left) with "Consecutive Login", "Rewards Received: n / 28" and Confirm (bottom right). Seen once a day, over the lobby just after it loaded following the date change. It's a lobby state rather than a common popup because only the lobby shows it.
  - Identified by "Rewards Received:" without the count (`info_lobby_checkin-text_1420-882-260-44.png`), since the count changes daily: 1.0 on the dialog, at most 0.22 elsewhere.
  - Closed by Confirm (`btn_lobby_checkin-confirm_1530-965-170-60.png`, centre (1615, 995)): 1.0 on the dialog, at most 0.33 elsewhere. Confirm opens checkin-received, not the lobby.
  - The main-menu icon still matches (1.0), undimmed, and the barrel doesn't (0.76, behind Merurin's hat).
- **checkin-received**: "Received Check-In Reward", listing the day's reward, with "Tap to close" at the bottom.
  - Identified by its title (`info_lobby_checkin-received-title_675-170-570-65.png`): 1.0 on the dialog, at most 0.34 elsewhere.
  - Closed by "Tap to close" (`btn_lobby_checkin-received-close_860-1000-200-80.png`, centre (960, 1040)), lower than the common popups' own: 1.0 on the dialog, at most 0.35 elsewhere. Closing it leaves the lobby active.
  - The main-menu icon still matches (1.0), and the barrel doesn't (0.49).

Why the barrel: The score does not change much under all known conditions of the lobby - it scores 1.0 by day, 0.96 at night, 0.99 at rest and 0.96 under `main-menu`, and at most 0.30 on non-lobby screens.

Behaviour:
- The lobby falls back to rest on its own after a few seconds idle (~9 s observed); `start-screen` opens it at rest.
- After loading, a chat toast "You have entered channel #N." (white bubble just below the top-right icons) shows for ~4 s. It doesn't cover the 4-boxes icon, which still matches.
- Activate by tapping the main-menu icon's spot, (1869, 49), until the icon shows. If the tap opens `main-menu` instead, the panel's X sits on the same spot, so the next tap closes it and leaves the lobby active.
- Automated by `e7/routines/lobby.py` (`python -m e7.bot lobby`).

## sanctuary (`e7/templates/start-screen/lobby/sanctuary/`)

Opened by Sanctuary on the active lobby. Title "Sanctuary" with a back arrow top left; Forest of Souls, Heart of Orbis and Alchemist's Steeple listed on the right.

- Identified by its Forest of Souls entry (`btn_sanctuary_forest-of-souls_1625-238-235-52.png`, the text only, not the sparkle right of it), which also opens `forest-of-souls`. It scored 1.0 on two captures with different flashes behind it and no match on any other saved screen.
- The background art changes constantly: consecutive captures differ by 3–49%, so waiting for two identical screenshots never ends. The HUD and the list on the right stay still; judge settling by those.

## forest-of-souls (`e7/templates/start-screen/lobby/sanctuary/forest-of-souls/`)

Opened by Forest of Souls in `sanctuary`. Lists Penguin Nest, Spirit Well and MolaGora Farm with their timers, a Cultivate count, and Growth Altar.

- Identified by its title, top left (`info_forest-of-souls_title_98-26-260-52.png`): 1.0 on two captures and no match on any other saved screen, Sanctuary included.
- The timers and the Cultivate (2/3) count change, so they're for reading only, not for identifying the menu.
- The back arrow (top left) goes straight to the lobby, active, not back to `sanctuary`.
- The title still matches (1.0) under the reward dialog's dim, so it can't tell the dialog is closed (Rule 1).

Two states: the menu, and **reward** (`screen-reward.png`), a dialog over the dimmed menu.

Controls (task `claim-forest`, `e7/routines/claim_forest.py`, `python -m e7.bot claim_forest`):
- **Penguin Nest, Spirit Well, MolaGora Farm** rows: each shows "Receive Reward" (bright blue pill, orange dot) when ready, else a countdown on a dark pill. One image, `btn_forest-of-souls_receive-reward_1468-378-186-36.png` (the text only, without the sparkles either side), cut on Penguin Nest's row, matches every ready row at its offset: Spirit Well +174 px (1.0), MolaGora Farm +347 px. It scores at most 0.19 on a row with a timer, no match on MolaGora Farm resting, and 0.16 under the dialog.
- Tapping a ready Penguin Nest or Spirit Well opens the **reward** dialog: a title naming the reward ("A Penguin has fully grown!", "Lesser Spirit Bloom Growth Completed!"), the items got, and "Tap to close". The titles differ, but "Tap to close" (`btn_forest-of-souls_reward-close_860-765-200-90.png`, centre (960, 810)) sits in the same place on both, so it identifies the dialog and closes it: 0.97–1.0 on the dialog, at most 0.19 on every other saved screen, the common popups included (theirs sit higher). Closing it leaves the row on its timer.
- Tapping a ready MolaGora Farm opens **no dialog**: a "Skill Enhancer MolaGora" banner slides in at the top for a few seconds and the row turns to "MolaGora Farm (Resting Phase)" with a ~60 h countdown on a grey left half. So the routine counts a row as claimed once its Receive Reward is gone with no dialog open, not once a dialog showed.
- A blue ring shows where the screen was just tapped, for about a second. Over "Tap to close" it stops the button matching (no match on the capture right after a close tap), so a dialog can look closed for a moment while it's still open.
- **Cultivate (n/3)**: shows only while MolaGora Farm is growing. It's gone while the farm shows Receive Reward and while it rests, so a missing button means skip, not a failure. It takes 24 h off MolaGora Farm's timer (36:46 → 12:45) and opens no dialog. When no uses are left the button turns grey and loses its orange dot, and it can't be used again. `btn_forest-of-souls_cultivate_1622-810-155-48.png` still scores 0.96 on the grey button, so lit is told by colour: mean green minus blue over the button is +41 lit, -12 grey. The count "(2/3)" doesn't change between captures (mean pixel difference 0) and changes by 30 when it goes up.

## shop-landing and daily-shop (`e7/templates/start-screen/lobby/main-menu/shop-landing/`)

`shop-landing` is the Shop as it opens, on Update Special. Its side list (Update Special, Pack, Purchase Skystone, Shop, Exchange, Skin, Shop Event) changes which entries it shows: Web Store was listed below Update Special on one visit and gone on the next, which moved every entry below it up by ~118 px. `daily-shop` is the list's Shop entry, opened on its Normal tab.

- Both images on the list are `_anywhere`, searched over the whole screen, so they don't depend on which entries show:
  - `btn_shop-landing_daily-shop_35-670-145-44_anywhere.png` (scales icon and "Shop", unlit): 1.0 on `shop-landing` with Web Store, 0.93 without, and no match on any other saved screen, the lit entry on `daily-shop` included.
  - `info_daily-shop_tab-lit_33-632-152-56_anywhere.png` (the lit Shop entry) identifies `daily-shop`: 1.0 with Web Store, 0.96 without, at most 0.63 elsewhere (the lit Update Special on `shop-landing`).

`daily-shop` has three states: the product grid, **reward** (`screen-reward.png`) and **buy** (`screen-buy.png`), each a dialog over the dimmed grid.

The grid reorders: a product bought or claimed today moves to the end, its price pill turns to a grey "Purchase available in …" timer, and every card after it shifts back one place, until the daily reset. `screen.png` (from before a reset) shows the bought order. So nothing on the grid can be found at a fixed spot.

Controls (task `claim-daily-shop`, `e7/routines/claim_daily_shop.py`, `python -m e7.bot claim_daily_shop`: Free, then 40 Energy, then 5 Flags, then back to the lobby):
- **Free**: the green pill on "Complimentary Daily Product", first in the grid while unclaimed. Once claimed its Free badge fades too. `btn_daily-shop_free_540-515-130-45_anywhere.png` is searched over the whole screen. The crop takes in the green pill around the word: the word alone scored 0.85 on "Free Covenant…" in the lobby's check-in reward text. With the pill it's 1.0 on the unclaimed grid, 0.45 under the reward dialog, 0.43 on the claimed grid and at most 0.60 elsewhere. No Free means today's product is already claimed.
- Tapping Free opens **reward**: "Received Reward", "You have successfully purchased the product…", the items (150,000 gold, 40 bookmarks) and "Tap to close". Identified by its title (`info_daily-shop_reward-title_770-222-380-60.png`): 1.0 here, at most 0.48 elsewhere (forest-of-souls' reward dialog). Closed by "Tap to close" (`btn_daily-shop_reward-close_860-770-200-90.png`, centre (960, 815)): 1.0 here, but also 0.95 on forest-of-souls' reward dialog, whose "Tap to close" sits in the same place, so it closes the dialog but doesn't identify it. Closing it leaves the grid with the product claimed.
- **40 Energy, 5 Flags** (100 green hearts each, once a day): both show the same heart + "100" pill, and "40 Energy" also scores 0.88 on "20 Energy", so a card is found by its title and its pill is checked at an offset from it.
  - Titles, searched over the whole screen: `info_daily-shop_energy-40_545-245-40-32_anywhere.png` is the digits "40" only (1.0 on its card, 0.72 on "80 Energy", 0.65 on "20 Energy"); `info_daily-shop_flags-5_1165-243-85-36_anywhere.png` is "5 Flags" (1.0, at most 0.55 on other titles). The title stays on a bought card (0.92–1.0), and matches through a dialog's dim (0.98).
  - The pill (`btn_daily-shop_buy-100-hearts_540-515-130-45.png`, cut on 40 Energy) sits 277 px below the title's centre, +40 px right of "40"'s centre and straight below "5 Flags". There it scores 0.92–1.0 unbought, 0.23–0.25 bought (timer) and 0.17–0.61 under a dialog. So popups and dialogs are closed before the check (Rule 1).
  - Tapping the pill opens **buy**: "Buy", "Would you like to purchase this product?", the product's name, "Purchase Available: 1 time(s)", Cancel and a green [heart 100] Buy. Identified by its title (`info_daily-shop_buy-title_890-205-140-65.png`) and confirmed by `btn_daily-shop_buy-confirm_900-722-445-85.png` (the whole green button, centre (1122, 764)). Buy closes the dialog with no reward dialog after it. The hearts drop by 100 and the card moves to the end of the grid, but only a moment after the dialog closes: a check right after still saw the price, so the routine waits up to 5 s for it to go.

## arena-landing, arena, arena-team and arena-battle (`e7/templates/start-screen/lobby/main-menu/arena-landing/`)

`arena-landing` is the Arena hub, opened by Arena in `main-menu` (`btn_main-menu_arena-landing_1195-562-96-46.png`, the text only, without the orange dot left of it: 1.0 on `main-menu`, at most 0.44 elsewhere). It shows World Arena's season and Top Player Matchup, with four cards along the bottom: Draft Arena, Arena, World Arena and World Arena Tournament. Named like `shop-landing`: the menu the game lands on before the one the tasks use. `arena` is the bottom Arena card's menu: the opponent list, with season, rank, Weekly Play Rewards, Defense Team, Arena Shop and Battle Pass on the left, three opponents with Refresh and Challenge in the middle, and tabs on the right (Opponents, NPC Challenge, Battle Log, Rank, Hall of Fame, Arena Story). The top bar shows the arena flags as `n/5` (one per fight; it can go over 5).

- `arena-landing` and `arena` show the same title, "Arena" with a back arrow top left, so the title identifies neither.
- `arena-landing` is identified by its Arena card (`btn_arena-landing_arena_650-985-110-45.png`, the word "Arena" on the card), which also opens `arena`: 1.0 on `arena-landing`, at most 0.33 elsewhere.
- `arena` is identified by its Defense Team button (`info_arena_defense-team_125-785-210-50.png`, the text only): 1.0 on `arena` in every state seen, at most 0.41 elsewhere. It was seen on the Opponents tab only.

### arena: the opponent list

- **Rows** sit 192 px apart (tap points (720, 350 + 192·i)). Names and teams change on every refresh, so rows are tapped by position, never by image.
- A row turns **red** once its opponent has been fought and lost to. Matching can't see it; colour can: red minus blue over (760, 262 + 192·i, 90, 30) is +45 red, +7..+8 grey, with or without the gold highlight a chosen row gets. After a **win** the list resets to three new opponents, all grey.
- Tapping a row highlights it gold and lights **Challenge** (`btn_arena_arena-team_775-950-365-85.png`). The image scores 0.97 dim and 1.00 lit, so lit is told by colour: green minus blue over (800, 960, 315, 65) is +29 lit, +10 dim. A row tap right after a fight sometimes leaves Challenge dim; a second tap lights it.
- **Refresh** (top middle) shows "Free" (`info_arena_refresh-free_1310-150-90-50.png`: 1.0 on `arena`, at most 0.40 elsewhere) while a free refresh is available. Tapping it opens the **refresh** state (`screen-refresh.png`): "Would you like to refresh the opponent?" (`info_arena_refresh-question_695-405-530-50.png`), "Free refresh does not count toward daily refresh limit.", Cancel (`btn_arena_refresh-cancel_600-710-255-75.png`, the same button as `daily-shop`'s Buy dialog, 1.00 there) and a green [Free] Confirm (`btn_arena_refresh-confirm_1140-715-180-65.png`; the pill is `info_arena_refresh-confirm-free_960-722-150-50.png`). Each scores at most 0.49 elsewhere. After the free refresh, Refresh goes on a cooldown during which it can't be tapped; past ones count toward a daily limit and may cost, so the routine confirms only while the pill says Free. A win's list reset brought "Free" back.
- **Flags at 0** (`screen-flags-0.png`): `info_arena_flags-0_740-30-36-42_white.png`, the "0" of the counter, matched white-only: 1.00 on 0/5, 0.75–0.77 on 10/5, 9/5 and 8/5, 0.46 on 1/5. Rounded digits come close, so the routine asks for 0.95 instead of 0.85. 2–6 weren't seen.

### arena-team and arena-battle

- Challenge opens **`arena-team`** about 1–2 s later: Arena - Team 1–9 on the left, your team vs the opponent's, Team CP, the win's point gain, a hero list on the right, and Start with a flag counter `1/n`. Identified by Start (`btn_arena-team_arena-battle_1180-960-180-65.png`, the word only, without the counter): 1.0 on `arena-team`, at most 0.45 elsewhere.
- Start opens **`arena-battle`** after a load (a blue diamond, then the battle, ~6–9 s in all). Start flickers on and off for about a second after a tap that took, so a check that sees it gone, then back, taps it twice; the second tap lands on the load and does nothing.
- Every battle starts with **auto off**. Auto (`btn_arena-battle_auto_1660-18-62-64.png`, the A in a circle of arrows, top right left of chat and pause) turns it on. While it's on, the arrows spin: the image scored 0.95–1.00 on still (off) icons and 0.62 on a spinning one. A battle left on manual waits on the hero's turn with three skill buttons bottom right; with auto on, the bottom right shows the four heroes' portraits with check marks instead. In 3 of 8 battles the first Auto tap, ~0.5 s after the battle view showed, didn't take: Auto still matched 3 polls in a row afterwards, and a second tap turned auto on. Skill cutscenes (full-screen art, some greyscale) cover the battle view; nothing matches on them.
- Battles took 1–2 min. They end on the **results** state (`screen-results.png`): DEFEAT or a win banner, Victory Points with the change (-8 on a defeat), exp, Battle Results and Confirm. Identified by "Victory Points" (`info_arena-battle_victory-points_855-610-210-45.png`) with Confirm (`btn_arena-battle_arena_1630-950-250-85.png`), which sits in the same place on a win and a defeat: each 1.0 on results, at most 0.36 elsewhere. Confirm goes back to `arena`.

Task `run-arena` (`e7/routines/run_arena.py`, `python -m e7.bot run_arena`): fights until the flag counter shows 0. Each round takes the first row that isn't red; with all three red it uses the free Refresh, and stops if Refresh isn't free. Then Challenge, Start, Auto (tapped again if it's still not spinning after 3 polls), Confirm. Once it stops, it goes back to the lobby. `python -m e7.routines.run_arena --fights N` stops after N fights.

- While a run and recon both captured every second, BlueStacks' memory grew from 9.6 GB to 22 GB in ~45 min, then every screencap came back empty (all bytes 0, BlueStacks in focus and responding) until it was restarted.

## battle and hunt (`e7/templates/start-screen/lobby/main-menu/battle/`)

`battle` is opened by Battle in `main-menu` (`btn_main-menu_battle_1192-465-100-46.png`, the word only, without the EVENT badge above it: 1.0 on `main-menu`, at most 0.38 elsewhere). It has three tabs, Normal, Seasonal and Event (Event locked), and opens on Normal. The Normal tab is a row of cards: Dimensional Exploration, Spirit Altar, Hunt, Labyrinth, and a fifth card cut off at the right edge. Spirit Altar and Hunt carried EVENT badges with drop-rate bonuses.

`hunt` is the Hunt card's menu. On the left are a big "Hunt" heading, Obtainable Sets and Exclusive Reward. In the middle are the difficulties Hunt - Normal, Hard, Hell and Otherworldly Hunt, each with a "Complete" or "Available" line. On the right, under "Available Dungeons", is a list of hunt cards: Wyvern, Golem, Banshee, Azimanak, Caides and Ogre, in that order.

- Both menus show the same title, "Battle" with a back arrow top left, so the title identifies neither.
- `battle` is identified by the Hunt card's title (`btn_battle_hunt_1044-282-70-40.png`, the word only, without the dragon icon or EVENT badge), which also opens `hunt`: 1.0 on `battle`, at most 0.63 elsewhere (`auto`'s complete dialog).
- `hunt` is identified by its "Hunt" heading (`info_hunt_title_54-228-118-56.png`): 1.0 in all six states, at most 0.34 elsewhere. Hunt - Hell can't identify it: the ogre state has no Hell.

### hunt: the six states

One state per hunt card: wyvern (`screen.png`), golem, banshee, azimanak, caides and ogre (`screen-<hunt>.png`). Tapping a card makes it the chosen hunt, framed gold.

- Each state is told by its first Exclusive Reward icon, bottom left (`info_hunt_<hunt>-reward_98-930-100-100.png`): 1.0 on its own state, at most 0.36 on the others and elsewhere.
- **Cards** are cut on their label text ("Golem Hunt") and are `_anywhere` (`btn_hunt_<hunt>_*_anywhere.png`), because the list scrolls on its own: choosing a card scrolls it to just below the card before it. Each label scores 1.0 wherever it shows and at most 0.74 elsewhere. Labels sit 306 px apart.
- With a card chosen, the next card below shows only its top, and its label is cut off at the screen's bottom edge, too little to match. A tap on that sliver (one card step below the chosen label) chooses it, so no swipe is needed to reach the last cards. Going up works the same way: tapping the top showing card brings the one before it into view.
- **Ogre** shows only Otherworldly Hunt: no Normal, Hard or Hell. Its reward is a red "?" box (level 85) and a crystal. Not automated yet.
- **Hunt - Hell** (`btn_hunt_hunt-team_1170-578-142-42.png`, the text without its Complete line) opens `hunt-team` for the chosen hunt: 1.0 in the five states that have it, at most 0.40 elsewhere.

## hunt-team (`e7/templates/start-screen/lobby/main-menu/battle/hunt/hunt-team/`)

Titled "Ready". Hunt - Team 1–6 on the left, the team with its pet in the middle, the stage top right ("Wyvern Hunt / Hunt - Hell", following the hunt chosen on `hunt`) with Obtainable Rewards, Quick Battling (daily chances, a 200-stamina button) bottom right, and Manage Team, Recommended Formation, Boss Guide and Background Battling along the bottom.

- Identified by the "Quick Battling" label (`info_hunt-team_quick-battling_1446-682-176-40.png`): 1.0 on the menu, 0.32 under its dialogs, at most 0.41 elsewhere.
- The date-changed popup's `screen.png` was captured over this menu, so Background Battling scores 0.93 there.
- The "0" at the start of the top bar scores 0.91 against arena's `info_arena_flags-0` (white-only), so `where` names `arena` here too. `run_arena` asks 0.95 of that image.

Three states: the menu, **background-battling** and **confirm**.

- **Background Battling** (`btn_hunt-team_background-battling_918-838-130-56.png`, the text without its icon) opens the background-battling dialog (`screen-background-battling.png`). But while a background battle is running, it opens `auto`'s **running** state instead, which has a Stop button.
- **background-battling**: "Background Battling" (`info_hunt-team_dialog-title_428-86-326-54.png`: 1.0 on this dialog and on confirm, at most 0.33 elsewhere), your stamina and leifs top right, tabs Register Background Battling and Auto-Arrange Equipment Settings, the stage, Currency Consumed per Run (20 stamina or 0.25 leifs), **Use Owned Energy First**, **Leifs to be Used** (Min, -1, n/max, +1, Max, a slider), the total cost (stamina, leifs) with Estimated Completions and Time, a green **Start**, and "Tap to close" below (`btn_hunt-team_dialog-close_870-1020-180-44.png`: also 1.0 on the lobby's check-in-received, so it closes but doesn't identify).
  - **Use Owned Energy First**: unticked (`btn_hunt-team_use-energy-first_835-461-46-46.png`) and ticked, a green check (`info_hunt-team_use-energy-first-ticked_835-461-46-46.png`). Each scores 1.0 on its own state and 0.26–0.29 on the other. The game keeps it ticked between visits. It can be greyed out, which hasn't been seen yet.
  - Unticked, each step of the count is 1 leif (4 runs). Ticked, each step is 80 stamina (4 runs) while stamina covers it, then 1 leif. With 449 stamina and 7 leifs the max was 12: 5 stamina steps and 7 leif steps. 5/12 showed 400 stamina, 0 leifs, ~20 completions, ~16 min; 6/12 showed 400 stamina and 1 leif.
  - The leif cost's "0" (`info_hunt-team_leif-cost-0_1242-752-36-38_white.png`) scores 1.0 on 0 and 0.49 on 1.
  - +1 (`btn_hunt-team_plus-1_1312-619-76-50.png`) and -1 (`btn_hunt-team_minus-1_920-619-78-50.png`) step the count by one. -1 exactly undoes a +1. A step that changed the count changes the count's box (1080, 615, 170, 60) by a mean of 5.9–7.4; an unchanged count gives 0.0.
- **confirm** (`screen-confirm.png`): Start (`btn_hunt-team_start_786-905-343-72.png`) opens "Would you like to start Background Battling?" (`info_hunt-team_start-question_670-462-580-50.png`: 1.0 here, at most 0.48 elsewhere) with Cancel and Confirm (`btn_hunt-team_start-confirm_975-647-293-86.png`). Confirm is the same button as the lobby quit dialog's (1.0 there), so it's tapped only once the question shows. Confirm closes both dialogs, spends the cost and starts the battle. The HUD clock then shows, spinning.

Task `hunt` (`e7/routines/hunt.py`, `python -m e7.bot hunt`): starts Background Battling on Wyvern, Hunt - Hell, paid with stamina only. `python -m e7.routines.hunt --hunt NAME --leifs N` picks another hunt and adds N leif steps. Ogre is refused.

- It first checks the lobby's HUD clock. If the clock is spinning, a battle is running: it stops without starting anything.
- On the dialog it ticks Use Owned Energy First (going on without it when it won't tick), then taps +1 while the leif cost shows 0. With 0 leifs it takes back the first leif step with -1. If even the first step costs a leif, stamina is too low, so it closes the dialog and counts that as success.
- If Background Battling opens auto's running state after all, it closes that with "Tap to close." and stops.
- Tested on a running battle: it stopped at the clock check; with the clock check skipped, it chose caides and then wyvern and stopped on the running state. Ticking, the count and Start haven't been run by the routine yet.

## orbis-guide (`e7/templates/start-screen/lobby/main-menu/orbis-guide/`)

A panel over the dimmed lobby, opened by Orbis Guide in `main-menu`. Tap its **icon** (`btn_main-menu_orbis-guide_1398-172-70-70.png`, centre ~(1433, 207)): two taps on the "Orbis Guide" label under it did nothing. The icon scores 1.0 on `main-menu` and at most 0.66 elsewhere. The panel has tabs on the left (Three Sisters' Diary, A Journey of Succession, Currency Details, Guide, Journey Through World Arena) and "Tap to close" at the bottom, which hasn't been tapped yet. It opens on Three Sisters' Diary: a reputation total, a bar with chests at 10, 20, 30, 50, 80 and 100, and below it the daily missions ("[Daily] Use Spectral Core I", "Level Up Hero", "Enhance Equipment"…), each with a 0/1 count and a Go button.

- Identified by its title, top left (`info_orbis-guide_title_98-95-235-60.png`): 1.0 on the panel, at most 0.42 elsewhere. It still matches under the reward dialog (1.0) and the date-changed popup (0.99), so popups are closed before trusting it (Rule 1).
- **Chests**: a ready chest carries an orange badge at its top left. Tapping one claims every ready chest on the bar at once: after a tap on the 100 chest, all six showed check marks. The chest image (`btn_orbis-guide_chest-100_1742-124-60-60.png`, cut without the badge) scores 1.0 on a ready chest and 0.57 on a claimed one under the dialog. A claimed chest without the dim hasn't been captured. Ready is told by colour: mean red minus blue over the badge (1729, 113, 14, 14) is +205 lit, -4..+5 on every other capture.
- **reward** (`screen-reward.png`): "Reputation Point Rewards", "You have received rewards for your total Reputation Points.", the items (140,000 gold, 50 hearts, 65 skystones and three more) and "Tap to close". Identified by its title (`info_orbis-guide_reward-title_685-222-550-62.png`): 1.0 here, 0.64 under date-changed, at most 0.31 elsewhere. Closed by "Tap to close" (`btn_orbis-guide_reward-close_860-750-200-90.png`, centre (960, 795)), cut from the capture but not yet tapped. It scores 0.96–0.99 on forest-of-souls', daily-shop's and date-changed's "Tap to close", so it closes the dialog but doesn't identify it.

Task `claim-dailies` (`e7/routines/claim_dailies.py`, `python -m e7.bot claim_dailies`): goes to orbis-guide, taps the 100 chest only while its badge is lit, closes the reward dialog, then goes back to the lobby. No badge means nothing to claim (already claimed, or under 100 points), and that counts as success. A run on an already-claimed day passed. The claim branch hasn't been run by the routine yet.

## HUD (`e7/templates/common/hud/`)

The icon row along the top right (clock, bell, inventory, mail, chat, main menu) is the same on every menu with a HUD: the active lobby, `main-menu`, `shop-landing`, `daily-shop`, `sanctuary` and `forest-of-souls`. `screen.png` is the active lobby. Its elements live in `common/` because no one menu owns them.

- **Clock** (`btn_hud_auto_1388-12-72-68.png`, centre ~(1424, 46), left of the bell): white clock in a circle of two arrows, opens `auto`. It shows in two cases. While a background battle runs, the arrows turn and an orange glow sweeps round them, with no badge. While rewards wait, the clock is still, with the orange badge. Once the rewards are claimed it's gone, and the stamina, gold and gem counters shift ~80 px right into its place. So no clock on an active HUD means nothing to claim.
  - The still clock matched 0.99–1.0 on every saved screen with the HUD, under the quit dialog's and popups' dim too, and none on the lobby at rest, the check-in dialog, the start screen or the lobby after the claim (0.13). The spinning clock matched on 1 of 6 frames (0.88), so matching can't see it reliably. `sanctuary`'s capture shows it spinning.
  - **Spinning** is told by change between frames: over (1388, 12, 72, 68), two frames 0.3 s apart differ by a mean of 38–49 while it spins, against 0.0–0.1 on the HUD's still icons. Both frames need the HUD up (the lobby's main-menu icon), since the lobby hides the HUD within seconds.
  - The lobby's HUD can fall back to rest between the routine waking it and the tap on the clock. The tap then only wakes the HUD and `auto` doesn't open.
- **Orange badge**: a dot over the clock's top left, seen on every capture with the clock. The crop includes it, but the match can't tell the badge is lit: it scores the same under a dim. Tell it by colour instead: mean red minus blue over (1392, 17, 14, 14) is +207 lit, at most +80 on every other saved screen (+30 dimmed).

## auto (`e7/templates/common/auto/`)

"Background Battling": a dialog over the dimmed screen, opened by the HUD clock. Shows the battle's stage (e.g. Hunt - Hell), Battle Progress, four tiles (Elapsed Time, Acquired Equipment, Sell, Acquired Gold), Acquired Currency, a green button, and "Tap to close." below the panel. It lives in `common/` because the clock opens it from any menu's HUD.

- Identified by its title (`info_auto_title_778-76-366-58.png`): 1.0 on auto, 0.75 under Calculation Complete, at most 0.39 elsewhere. The lobby's main-menu icon and barrel don't match under it.

Four states:
- **running** (`screen-running.png`): a battle still going, opened by `hunt-team`'s Background Battling (the clock presumably opens it too). It shows the stage, a scene strip, Battle Progress n/m, the four tiles, a note that it goes on with the game closed, the loot so far, and a blue **Stop** button, which ends the battle early and settles the rewards. The title still matches (1.0). Never tap Stop. "Tap to close." (960, 1041), well below Stop, closes it back to the menu underneath.
- **unclaimed** (`screen.png`): the green button is **Calculate** (`btn_auto_calculate_780-908-370-70.png`, orange dot at its top left, left out of the crop): 1.0 here, 0.55 on Close, at most 0.33 elsewhere. It opens complete.
- **complete** (`screen-complete.png`): "Calculation Complete" over auto, listing the rewards ("items have been distributed", equipment goes to the Inventory). Event-mission toasts can slide in on the left. Identified by its title (`info_auto_complete-title_726-156-468-64.png`): 1.0 here, at most 0.40 elsewhere. Closed by "Tap to close" (`btn_auto_complete-close_860-835-200-95.png`, centre (960, 880)): 1.0 here, 0.80 on friendship-point-notification (below the 0.85 threshold), at most 0.22 elsewhere. Closing it leaves auto claimed.
- **claimed** (`screen-claimed.png`): the tiles show blue check marks and the green button is **Close** (`btn_auto_close_780-908-370-70.png`, no orange dot): 1.0 here, 0.55 on Calculate, at most 0.34 elsewhere. Close goes back to the menu the clock was tapped on (the lobby, active), now without the clock.

Task `claim-auto` (`e7/routines/claim_auto.py`, `python -m e7.bot claim_auto`): from the active lobby, tap the clock, Calculate, Tap to close, Close. No clock on the HUD means nothing to claim (success). No Calculate on auto means failure.

## date-changed popup (`e7/templates/common/popups/date-changed/`)

"Date Changed" / "The date has changed, proceeding to Lobby." with "Tap to close" and a down chevron below. Shows over whatever menu is open when the server day rolls over.

- Identified by its title (`info_date-changed_title_800-295-320-70.png`, white text on the dark band), matched in colour. It scored 1.0 on the popup and at most 0.24 on every other saved screen.
- Closed by tapping "Tap to close" (`btn_date-changed_close_860-695-200-90.png`, centre (960, 740)).
- Closing it loads the lobby.

## disconnected popup (`e7/templates/common/popups/disconnected/`)

"Disconnected from server. Returning to the title screen." with "Tap to close" and a down chevron below, on the same dark band as date-changed but with no title.

- Identified by its message (`info_disconnected_message_590-460-740-50.png`): 1.0 on the popup, at most 0.39 elsewhere (the lobby's quit dialog).
- Closed by tapping "Tap to close" (`btn_disconnected_close_860-643-200-90.png`, centre (960, 688)), higher up than date-changed's, so each popup has its own close button.
- Closing it goes to the start screen.
