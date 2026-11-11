# E7 UI notes

How E7 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `e7/templates/` (see the map skill for the scheme). Add new menu notes here, not as notes.md files in the template folders. `e7/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `e7/`.

## start-screen (`e7/templates/start-screen/`)

The title screen ("Tap to Start"). Its one indicator is also its button: the copyright line "© Smilegate. All Rights Reserved." at the bottom centre (`btn_start-screen_lobby_805-1023-311-26_white.png`). Tapping it, like tapping anywhere, starts the game and loads the lobby at rest.

- The title art is animated, and its colours change behind the text, so the template matches only the text. It's matched on white glyphs (`_white`). Its PNG is also transparent everywhere except the letters and a 1 px ring of their dark outline, and `core.vision.find` ignores transparent pixels. It scores 1.0 on every start-screen capture, including one with different art behind the text, and at most 0.09 elsewhere. A plain white crop of the line (no transparency) drops to ~0.78 when the art behind it changes.
- The template was built from two captures with different art behind the text. Its letter pixels are white in both, and its ring pixels are white in neither. To rebuild it, do the same; don't just crop one capture.
- Don't use the corner icons (Repair Resources, Global, key) or "Tap to Start" as indicators. The icons are translucent over the moving art and drop below the threshold. "Tap to Start" pulses. The corner HUD is sometimes drawn at about 0.83× size.
- Automated by `e7/routines/start_screen.py` (`python -m e7.bot start_screen`).

## lobby (`e7/templates/start-screen/lobby/`)

Three states: active and rest, each seen by day and by night, and quit. The scene's lighting changes with the time of day: at night the tavern is warmer and brighter. `screen.png` is the night lobby, active (the usable state). `screen-day.png` is the day lobby, active. `screen-night.png` is the night lobby, at rest. `screen-rest.png` is the day lobby, at rest. `screen-quit.png` is the quit dialog over the lobby.

- **active**: HUD shown. Identified by the barrel **and** `btn_lobby_sanctuary_27-246-112-86.png` (Sanctuary, left; also opens `sanctuary`) **and** `btn_lobby_main-menu_1847-20-45-58.png` (blue 4-boxes, top right; also opens the main menu). Neither icon is enough alone:
  - the 4-boxes icon also shows on other screens (e.g. the shop);
  - Sanctuary also shows on `main-menu`, a panel drawn over the lobby (there the 4-boxes icon is replaced by an X).
- **rest**: HUD hidden, only the animated tavern scene. Identified by `info_lobby_barrel_1240-140-80-120.png` (the big barrel on the wall right of the bar, centre ~(1280, 200)) while both the 4-boxes and Sanctuary icons are missing. The barrel is part of the scene, so it shows in every state and on `main-menu` (hence Sanctuary must be missing too). It's covered by some popups and absent on the shop and start screens.
- **quit**: "Are you sure you want to quit the game?" with Cancel (left, brown) and Confirm (right, blue), over the dimmed lobby. Escape in the lobby opens it, so the `lobby` routine opens it whenever it presses Back one time too many. It's a lobby state rather than a common popup because only the lobby opens it, and always on Escape.
  - Identified by its Cancel button (`info_lobby_quit-cancel_660-650-280-80.png`, same crop as `btn_lobby_lobby_...`, the tap back to the active lobby). Scored 1.0 on the dialog and no match on any other saved screen.
  - Close it with Cancel, never Confirm (Confirm quits the game).
  - The wall barrel still matches through the dim (0.96). The HUD icons don't.

Why the barrel: it scores 1.0 by day, 0.96 at night, 0.99 at rest and 0.96 under `main-menu`, and at most 0.30 on non-lobby screens. The heroes (e.g. the old man's belt, 520,660) match even better day to night (0.99), as they aren't relit. But they're the player's lobby characters and could change, and they're hidden under `main-menu`. If another lighting turns up (e.g. dusk), check the barrel on it.

Behaviour:
- The lobby falls back to rest on its own after a few seconds idle (~9 s observed); `start-screen` opens it at rest.
- Activate by tapping the main-menu icon's spot, (1869, 49), until the icon shows. If the tap opens `main-menu` instead, the panel's X sits on the same spot, so the next tap closes it and leaves the lobby active. Don't tap the floor spot (1600, 900) when the HUD may be up: it's right at the edge of the promo banner at the bottom right (~1560–1880, 905–1040).
- Escape from daily-shop goes to shop-landing, then a second Escape lands in the lobby already active.
- Tap the wanted lobby button right after activating; don't pause for screenshots or the tap lands on the resting lobby and does nothing.
- Automated by `e7/routines/lobby.py` (`python -m e7.bot lobby`).

## sanctuary (`e7/templates/start-screen/lobby/sanctuary/`)

Opened by Sanctuary on the active lobby. Title "Sanctuary" with a back arrow top left; Forest of Souls, Heart of Orbis and Alchemist's Steeple listed on the right.

- Identified by its Forest of Souls entry (`btn_sanctuary_forest-of-souls_1625-238-235-52.png`, the text only, not the sparkle right of it), which also opens `forest-of-souls`. It scored 1.0 on two captures with different flashes behind it and no match on any other saved screen.
- The background art (crystal tree and sky) flashes without pause: consecutive captures differ by 3–49%, so waiting for two identical screenshots never ends. The HUD and the list on the right stay still; judge settling by those.

## forest-of-souls (`e7/templates/start-screen/lobby/sanctuary/forest-of-souls/`)

Opened by Forest of Souls in `sanctuary`. Lists Penguin Nest, Spirit Well and MolaGora Farm with their timers, a Cultivate count, and Growth Altar.

- Identified by its title, top left (`info_forest-of-souls_title_98-26-260-52.png`): 1.0 on two captures and no match on any other saved screen, Sanctuary included.
- The timers and the Cultivate (2/3) count change, so they're for reading only, not for identifying the menu.
- The back arrow (top left) goes straight to the lobby, active, not back to `sanctuary`.

## date-changed popup (`e7/templates/common/popups/date-changed/`)

"Date Changed" / "The date has changed, proceeding to Lobby." with "Tap to close" and a down chevron below. Shows over whatever menu is open when the server day rolls over; first seen over the Wyvern Hunt team screen.

- Identified by its title (`info_date-changed_title_800-295-320-70.png`, white text on the dark band), matched in colour. It scored 1.0 on the popup and at most 0.24 on every other saved screen. Only seen over one screen so far; the band is translucent but dark enough behind the title that the background barely shows.
- Closed by tapping "Tap to close" (`btn_date-changed_close_860-695-200-90.png`, centre (960, 740)); one tap is enough.
- Closing it loads the lobby, and the disconnected popup follows straight away (below). Expect to end up on the start screen, not in the menu you were in.

## disconnected popup (`e7/templates/common/popups/disconnected/`)

"Disconnected from server. Returning to the title screen." with "Tap to close" and a down chevron below, on the same dark band as date-changed but with no title. Seen over the lobby right after closing date-changed.

- Identified by its message (`info_disconnected_message_590-460-740-50.png`): 1.0 on the popup, at most 0.39 elsewhere (the lobby's quit dialog).
- Closed by tapping "Tap to close" (`btn_disconnected_close_860-643-200-90.png`, centre (960, 688)), higher up than date-changed's, so each popup has its own close button.
- Closing it goes to the start screen.
- The lobby shows dimmed behind it and the wall barrel still matches (0.98).
