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
  - Tapping the pill opens **buy**: "Buy", "Would you like to purchase this product?", the product's name, "Purchase Available: 1 time(s)", Cancel and a green [heart 100] Buy. Identified by its title (`info_daily-shop_buy-title_890-205-140-65.png`) and confirmed by `btn_daily-shop_buy-confirm_900-722-445-85.png` (the whole green button, centre (1122, 764)). Buy closes the dialog with no reward dialog after it. The hearts drop by 100 and the card moves to the end of the grid.

## arena and arena-normal (`e7/templates/start-screen/lobby/main-menu/arena/`)

`arena` is the Arena hub, opened by Arena in `main-menu` (`btn_main-menu_arena_1195-562-96-46.png`, the text only, without the orange dot left of it: 1.0 on `main-menu`, at most 0.44 elsewhere). It shows World Arena's season and Top Player Matchup, with four cards along the bottom: Draft Arena, Arena, World Arena and World Arena Tournament. `arena-normal` is the bottom Arena card's menu: the opponent list, with season, rank, Weekly Play Rewards, Defense Team, Arena Shop and Battle Pass on the left, three opponents with Refresh and Challenge in the middle, and tabs on the right (Opponents, NPC Challenge, Battle Log, Rank, Hall of Fame, Arena Story).

- Both menus show the same title, "Arena" with a back arrow top left, so the title identifies neither.
- `arena` is identified by its Arena card (`btn_arena_arena-normal_650-985-110-45.png`, the word "Arena" on the card), which also opens `arena-normal`: 1.0 on `arena`, at most 0.33 elsewhere.
- `arena-normal` is identified by its Defense Team button (`info_arena-normal_defense-team_125-785-210-50.png`, the text only): 1.0 on `arena-normal`, at most 0.41 elsewhere. It was seen on the Opponents tab only.

## HUD (`e7/templates/common/hud/`)

The icon row along the top right (clock, bell, inventory, mail, chat, main menu) is the same on every menu with a HUD: the active lobby, `main-menu`, `shop-landing`, `daily-shop`, `sanctuary` and `forest-of-souls`. `screen.png` is the active lobby. Its elements live in `common/` because no one menu owns them.

- **Clock** (`btn_hud_auto_1388-12-72-68.png`, centre ~(1424, 46), left of the bell): white clock in a circle of two arrows, opens `auto`. It shows only while Background Battling has rewards waiting: once they're claimed it's gone, and the stamina, gold and gem counters shift ~80 px right into its place. So no clock on an active HUD means nothing to claim.
  - It matched 0.99–1.0 on every saved screen with the HUD, under the quit dialog's and popups' dim too, and none on the lobby at rest, the check-in dialog, the start screen, `sanctuary` (an orange glow sweeps around the clock there) or the lobby after the claim (0.13).
  - The lobby's HUD can fall back to rest between the routine waking it and the tap on the clock. The tap then only wakes the HUD and `auto` doesn't open.
- **Orange badge**: a dot over the clock's top left, seen on every capture with the clock. The crop includes it, but the match can't tell the badge is lit: it scores the same under a dim. Tell it by colour instead: mean red minus blue over (1392, 17, 14, 14) is +207 lit, at most +80 on every other saved screen (+30 dimmed).

## auto (`e7/templates/common/auto/`)

"Background Battling": a dialog over the dimmed screen, opened by the HUD clock. Shows the battle's stage (e.g. Hunt - Hell), Battle Progress, four tiles (Elapsed Time, Acquired Equipment, Sell, Acquired Gold), Acquired Currency, a green button, and "Tap to close." below the panel. It lives in `common/` because the clock opens it from any menu's HUD.

- Identified by its title (`info_auto_title_778-76-366-58.png`): 1.0 on auto, 0.75 under Calculation Complete, at most 0.39 elsewhere. The lobby's main-menu icon and barrel don't match under it.

Three states:
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
