# E7 UI notes

How E7 menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `e7/templates/` (see the pathfind skill for the scheme). Add new menu notes here, not as notes.md files in the template folders. `e7/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `e7/`.

## start-screen (`e7/templates/start-screen/`)

The title screen ("Tap to Start"). Its one indicator is also its button: the copyright line "© Smilegate. All Rights Reserved." at the bottom centre (`btn_start-screen_lobby_805-1023-311-26_white.png`). Tapping it, like tapping anywhere, starts the game and loads the lobby at rest.

- The title art is animated, and its colours change behind the text, so the template matches only the text. It's matched on white glyphs (`_white`). Its PNG is also transparent everywhere except the letters and a 1 px ring of their dark outline, and `core.vision.find` ignores transparent pixels. It scores 1.0 on every start-screen capture, including one with different art behind the text, and at most 0.09 elsewhere. A plain white crop of the line (no transparency) drops to ~0.78 when the art behind it changes.
- The template was built from two captures with different art behind the text. Its letter pixels are white in both, and its ring pixels are white in neither. To rebuild it, do the same; don't just crop one capture.
- Don't use the corner icons (Repair Resources, Global, key) or "Tap to Start" as indicators. The icons are translucent over the moving art and drop below the threshold. "Tap to Start" pulses. The corner HUD is sometimes drawn at about 0.83× size.
- The `start_screen` routine (`e7/routines/start_screen.py`, `python -m e7.bot start_screen`) waits up to 60 s for this screen or the lobby. It taps the copyright line until the screen goes, then waits up to 30 s for the lobby's wall barrel. The `lobby` routine checks for this screen before every Back press and hands over to `start_screen` when it's up.

## lobby (`e7/templates/start-screen/lobby/`)

Two states, each seen by day and by night. The scene's lighting changes with the time of day: at night the candles are lit and the tavern is warmer and brighter. `screen.png` is the night lobby, active (the usable state). `screen-day.png` is the day lobby, active. `screen-night.png` is the night lobby, at rest. `screen-rest.png` is the day lobby, at rest.

- **active**: HUD shown. Identified by the barrel **and** `info_lobby_sanctuary_27-246-112-86.png` (Sanctuary, left) **and** `btn_lobby_main-menu_1847-20-45-58.png` (blue 4-boxes, top right; also opens the main menu). Neither icon is enough alone:
  - the 4-boxes icon also shows on other screens (e.g. the shop);
  - Sanctuary also shows on `main-menu`, a panel drawn over the lobby (there the 4-boxes icon is replaced by an X).
- **rest**: HUD hidden, only the animated tavern scene. Identified by `info_lobby_barrel_1240-140-80-120.png` (the big barrel on the wall right of the bar, centre ~(1280, 200)) while both the 4-boxes and Sanctuary icons are missing. The barrel is part of the scene, so it shows in both states and on `main-menu` (hence Sanctuary must be missing too). It's covered by popups and absent on the shop and start screens.

Why the barrel: it scores 1.0 by day, 0.96 at night, 0.99 at rest and 0.96 under `main-menu`, and at most 0.30 on non-lobby screens. Don't use the table candle (bottom left): it's unlit by day and lit at night, and a crop of one doesn't match the other (0.75–0.82). The heroes (e.g. the old man's belt, 520,660) match even better day to night (0.99), as they aren't relit. But they're the player's lobby characters and could change, and they're hidden under `main-menu`. If another lighting turns up (e.g. dusk), check the barrel on it.

Behaviour:
- The lobby falls back to rest on its own after a few seconds idle (~9 s observed); `start-screen` opens it at rest.
- Activate by tapping the table candle's spot, (198, 975), where no HUD button sits. One tap was enough in testing, day and night; the HUD shows within ~1.5 s. Don't use the floor spot (1600, 900) when the HUD may be up: it's right at the edge of the promo banner at the bottom right (~1560–1880, 905–1040).
- Tapping the candle while `main-menu` is open closes the panel and leaves the lobby active.
- Escape from daily-shop goes to shop-landing, then a second Escape lands in the lobby already active.
- Tap the wanted lobby button right after activating; don't pause for screenshots or the tap lands on the resting lobby and does nothing.
- The `lobby` routine (`e7/routines/lobby.py`, `python -m e7.bot lobby`) does all this: Back until the barrel shows (handing over to `start_screen` whenever the start screen is up), then tap the candle's spot until the HUD icons show. Before every Back press and candle tap it cancels the quit dialog if it's up (see quit-game below).

## quit-game popup (`e7/templates/common/popups/quit-game/`)

"Are you sure you want to quit the game?" with Cancel (left, brown) and Confirm (right, blue). Escape in the lobby opens it, so the `lobby` routine opens it whenever it presses Back one time too many.

- Identified by its Cancel button (`info_quit-game_cancel_660-650-280-80.png`, same crop as `btn_quit-game_close_...`). Scored 1.0 on the dialog and no match on any other saved screen.
- Close it with Cancel, never Confirm (Confirm quits the game).
- The lobby shows dimmed behind it and the wall barrel still matches (0.96), so barrel alone would say "lobby". The HUD icons don't match through the dim, and tapping the candle's spot does nothing while it's up.
- As a common popup, `core.nav.tap_until` also cancels it automatically before each tap.
