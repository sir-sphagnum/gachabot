# E7 UI notes

How E7 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `e7/templates/` (see the map skill for the scheme). Add new menu notes here, not as notes.md files in the template folders. `e7/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `e7/`.

## start-screen (`e7/templates/start-screen/`)

The title screen ("Tap to Start"). Its one indicator is also its button: the copyright line "© Smilegate. All Rights Reserved." at the bottom centre (`btn_start-screen_lobby_805-1023-311-26_white.png`). Tapping it, like tapping anywhere, starts the game and loads the lobby at rest.

- Automated by `e7/routines/start_screen.py` (`python -m e7.bot start_screen`).

## lobby (`e7/templates/start-screen/lobby/`)

Three states: active and rest, each seen by day and by night, and quit. The scene's lighting changes with the time of day: at night the tavern is warmer and brighter. `screen.png` is the night lobby, active (the usable state). `screen-day.png` is the day lobby, active. `screen-night.png` is the night lobby, at rest. `screen-rest.png` is the day lobby, at rest. `screen-quit.png` is the quit dialog over the lobby.

- **active**: HUD shown. Identified by the barrel **and** `btn_lobby_main-menu_1847-20-45-58.png` (blue 4-boxes, top right; also opens the main menu). Neither is enough alone: the barrel shows in every lobby state, and the 4-boxes icon also shows on other screens (e.g. the shop).
- **rest**: HUD hidden, only the animated tavern scene. Identified by `info_lobby_barrel_1240-140-80-120.png` (the big barrel on the wall right of the bar, centre ~(1280, 200)) while the 4-boxes icon is missing. The barrel is part of the scene, so it shows in every state and on `main-menu`. It's covered by some popups and absent on the shop and start screens.
- **quit**: "Are you sure you want to quit the game?" with Cancel (left, brown) and Confirm (right, blue), over the dimmed lobby. Escape in the lobby opens it, so the `lobby` routine opens it whenever it presses Back one time too many. It's a lobby state rather than a common popup because only the lobby opens it, and always on Escape.
  - Identified by its question (`info_lobby_quit-text_690-462-540-50.png`), matched in colour: 1.0 on the dialog, at most 0.45 elsewhere (the disconnected popup's message).
  - Closed by tapping Cancel (`btn_lobby_lobby_660-650-280-80.png`, back to the active lobby): 1.0 on the dialog, at most 0.29 elsewhere. Never tap Confirm: it quits the game.
  - Escape also closes it, but takes ~1.4 s to clear the text. Pressed again before that, it can land on the lobby and open the dialog again; a tap on Cancel can't.
  - The wall barrel still matches through the dim (0.96). The HUD icons don't.

Why the barrel: The score does not change much under all known conditions of the lobby - it scores 1.0 by day, 0.96 at night, 0.99 at rest and 0.96 under `main-menu`, and at most 0.30 on non-lobby screens.

Behaviour:
- The lobby falls back to rest on its own after a few seconds idle (~9 s observed); `start-screen` opens it at rest.
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
