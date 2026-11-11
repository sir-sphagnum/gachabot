# E7 UI notes

How E7 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `e7/templates/` (see the map skill for the scheme). Add new menu notes here, not as notes.md files in the template folders. `e7/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `e7/`.

## start-screen (`e7/templates/start-screen/`)

The title screen ("Tap to Start"). Its one indicator is also its button: the copyright line "© Smilegate. All Rights Reserved." at the bottom centre (`btn_start-screen_lobby_805-1023-311-26_white.png`). Tapping it, like tapping anywhere, starts the game and loads the lobby at rest.

- The title art is animated, and its colours change behind the text, so the template matches only the text. It's matched on white glyphs (`_white`). Its PNG is also transparent everywhere except the letters and a 1 px ring of their dark outline, and `core.vision.find` ignores transparent pixels. It scores 1.0 on every start-screen capture, including one with different art behind the text, and at most 0.09 elsewhere. A plain white crop of the line (no transparency) drops to ~0.78 when the art behind it changes.
- The template was built from two captures with different art behind the text. Its letter pixels are white in both, and its ring pixels are white in neither. To rebuild it, do the same; don't just crop one capture.
- Don't use the corner icons (Repair Resources, Global, key) or "Tap to Start" as indicators. The icons are translucent over the moving art and drop below the threshold. "Tap to Start" pulses. The corner HUD is sometimes drawn at about 0.83× size.
- The `start_screen` routine (`e7/routines/start_screen.py`, `python -m e7.bot start_screen`) waits up to 60 s for this screen or the lobby. It taps the copyright line until the screen goes, then waits up to 30 s for the lobby's wall barrel. The `lobby` routine checks for this screen before every Back press and hands over to `start_screen` when it's up.

## lobby (`e7/templates/start-screen/lobby/`)

Two states, each seen by day and by night. The scene's lighting changes with the time of day: at night the tavern is warmer and brighter. `screen.png` is the night lobby, active (the usable state). `screen-day.png` is the day lobby, active. `screen-night.png` is the night lobby, at rest. `screen-rest.png` is the day lobby, at rest.

- **active**: HUD shown. Identified by the barrel **and** `info_lobby_sanctuary_27-246-112-86.png` (Sanctuary, left) **and** `btn_lobby_main-menu_1847-20-45-58.png` (blue 4-boxes, top right; also opens the main menu). Neither icon is enough alone:
  - the 4-boxes icon also shows on other screens (e.g. the shop);
  - Sanctuary also shows on `main-menu`, a panel drawn over the lobby (there the 4-boxes icon is replaced by an X).
- **rest**: HUD hidden, only the animated tavern scene. Identified by `info_lobby_barrel_1240-140-80-120.png` (the big barrel on the wall right of the bar, centre ~(1280, 200)) while both the 4-boxes and Sanctuary icons are missing. The barrel is part of the scene, so it shows in both states and on `main-menu` (hence Sanctuary must be missing too). It's covered by popups and absent on the shop and start screens.

Why the barrel: it scores 1.0 by day, 0.96 at night, 0.99 at rest and 0.96 under `main-menu`, and at most 0.30 on non-lobby screens. The heroes (e.g. the old man's belt, 520,660) match even better day to night (0.99), as they aren't relit. But they're the player's lobby characters and could change, and they're hidden under `main-menu`. If another lighting turns up (e.g. dusk), check the barrel on it.

Behaviour:
- The lobby falls back to rest on its own after a few seconds idle (~9 s observed); `start-screen` opens it at rest.
- Activate by tapping the main-menu icon's spot, (1869, 49), until the icon shows. If the tap opens `main-menu` instead, the panel's X sits on the same spot, so the next tap closes it and leaves the lobby active. Don't tap the floor spot (1600, 900) when the HUD may be up: it's right at the edge of the promo banner at the bottom right (~1560–1880, 905–1040).
- Escape from daily-shop goes to shop-landing, then a second Escape lands in the lobby already active.
- Tap the wanted lobby button right after activating; don't pause for screenshots or the tap lands on the resting lobby and does nothing.
- The `lobby` routine (`e7/routines/lobby.py`, `python -m e7.bot lobby`) does all this: Back until the barrel shows, then tap the main-menu icon's spot with `core.nav.tap_until` until the icon shows. Before each Back it closes any common popup that's open, then looks again, and it hands over to `start_screen` whenever the start screen is up. It checks popups before the barrel because the quit dialog and the Disconnected popup both show over the lobby with the barrel still matching (see below).

## quit-game popup (`e7/templates/common/popups/quit-game/`)

"Are you sure you want to quit the game?" with Cancel (left, brown) and Confirm (right, blue). Escape in the lobby opens it, so the `lobby` routine opens it whenever it presses Back one time too many.

- Identified by its Cancel button (`info_quit-game_cancel_660-650-280-80.png`, same crop as `btn_quit-game_close_...`). Scored 1.0 on the dialog and no match on any other saved screen.
- Close it with Cancel, never Confirm (Confirm quits the game).
- The lobby shows dimmed behind it and the wall barrel still matches (0.96), so barrel alone would say "lobby". The HUD icons don't match through the dim.
- As a common popup, the `lobby` routine and `core.nav.tap_until` cancel it automatically.

## date-changed popup (`e7/templates/common/popups/date-changed/`)

"Date Changed" / "The date has changed, proceeding to Lobby." with "Tap to close" and a down chevron below. Shows over whatever menu is open when the server day rolls over; first seen over the Wyvern Hunt team screen.

- Identified by its title (`info_date-changed_title_800-295-320-70.png`, white text on the dark band), matched in colour. It scored 1.0 on the popup and at most 0.24 on every other saved screen. Only seen over one screen so far; the band is translucent but dark enough behind the title that the background barely shows.
- Closed by tapping "Tap to close" (`btn_date-changed_close_860-695-200-90.png`, centre (960, 740)); one tap is enough.
- Closing it loads the lobby, and the disconnected popup follows straight away (below). Expect to end up on the start screen, not in the menu you were in.

## disconnected popup (`e7/templates/common/popups/disconnected/`)

"Disconnected from server. Returning to the title screen." with "Tap to close" and a down chevron below, on the same dark band as date-changed but with no title. Seen over the lobby right after closing date-changed.

- Identified by its message (`info_disconnected_message_590-460-740-50.png`): 1.0 on the popup, at most 0.39 elsewhere (the quit dialog).
- Closed by tapping "Tap to close" (`btn_disconnected_close_860-643-200-90.png`, centre (960, 688)), higher up than date-changed's, so each popup has its own close button.
- Closing it goes to the start screen.
- The lobby shows dimmed behind it and the wall barrel still matches (0.98), so check for it before trusting the barrel. The `lobby` routine does.
