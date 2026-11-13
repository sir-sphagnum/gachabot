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

## HUD (`e7/templates/common/hud/`)

The icon row along the top right (clock, bell, inventory, mail, chat, main menu) is the same on every menu with a HUD: the active lobby, `main-menu`, `shop-landing`, `daily-shop`, `sanctuary` and `forest-of-souls`. `screen.png` is the active lobby. Its elements live in `common/` because no one menu owns them.

- **Clock** (`info_hud_clock_1388-12-72-68.png`, centre ~(1424, 46), left of the bell): white clock in a circle of two arrows. It matched 0.99–1.0 on every saved screen with the HUD, under the quit dialog's and popups' dim too, and none on the lobby at rest, the check-in dialog, the start screen or `sanctuary` (an orange glow sweeps around the clock there).
- **Orange badge**: a dot over the clock's top left. The crop includes it, but the match can't tell the badge is lit: it scores the same under a dim. Tell it by colour instead: mean red minus blue over (1392, 17, 14, 14) is +207 lit, at most +80 on every other saved screen (+30 dimmed). Every capture so far has the badge, so how the clock scores without it is untested.

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
