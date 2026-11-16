---
name: new-game
description: Set up a new game for the bot - its package folder (config, bot entry point, routines, templates, notes), then map its start screen, popups and lobby and write the start_screen and lobby routines that get it from launch into the lobby. Use when the user says "add game <name>", "new game <name>", "set up <name>", or similar.
---

# New game

A game is ready for the other skills (map, navigate, task) once it has:

- an entry in `core.device.GAMES`: short name to Android package name. The short name is also the game's folder and Python package.
- `<game>/templates/` with a `.gitkeep` (git ignores everything else under any `templates/`), and `common/popups/` in it for the game's popups.
- a menu folder named `lobby`, and `<game>/routines/lobby.py` whose `run()` brings the game there from anywhere, with its HUD showing, and returns True once it has. `core.nav` starts every walk with it.
- a `start_screen` routine in `<game>.routines.ROUTINES`, which `core.device restart` runs after starting the game.

Part 1 creates the files with a script. Part 2 maps the screens from launch to the lobby and writes the two routines. Run all commands from the project root. E7 (`e7/`) is the worked example: read `e7/CLAUDE.md` and its notes before Part 2.

## Part 1: the package

1. Ask the user which game, unless they said. Have them open it in BlueStacks, then find its package: `python -m core.device focus` prints the package in focus. If the game isn't installed, stop and tell them.
2. Agree on a short name: lowercase letters, digits and `_` (e.g. `e7`, `re1999`). `core.device.GAMES` may already list the game under a short name that has no folder yet; use that name, or rename its key there if the user wants another (the script refuses a package that is already listed under another name).
3. Run:
   ```
   python -m tools.new_game <game> <package> --title "<Game's Name>"
   ```
   `--title` is the name the generated files write (e.g. `"Reverse: 1999"`); without it they get the short name title-cased. It adds the `GAMES` entry, creates `<game>/` (`config.py`, `bot.py`, `routines/` with an empty `ROUTINES`, `templates/`, `notes/UI.md`, `notes/routines.md`, `CLAUDE.md`) and refuses if the folder already exists. It writes no start_screen or lobby routine: those come in Part 2.

## Part 2: from launch to the lobby

1. Open this run's log: `python -m core.log start new-game`. If it says `(inside <skill>)` and you didn't start that skill in this conversation, run `python -m core.log end --all` and start again (`.claude/logging.md` §5). Check `python -m core.device health` and wait for the user if it fails.
2. Force-stop and launch the game, so it comes up on its start screen: `python -m core.device stop <game>`, then `python -m core.device start --fullscreen <game>`.
3. **Start screen, popups and lobby.** Follow the map skill (`.claude/skills/map/SKILL.md`) from its Start step, with its log already open. The first screen past the loading screens is the root menu, `start-screen`. The user clicks into the game; the menu reached once the popups after START are closed becomes `lobby` (use that name, `core.nav` looks for it). Before mapping, tell the user that mapping the first launch of the day uses up its popups (login rewards, check-ins, event sign-ins): the routines can only be tested against them on the next day's first launch (step 6). Along the way:
   - **Start screen identifier:** something that is always there and never changes, like E7's copyright line. A "Tap to Start" label that pulses needs `_white` or an alpha mask. If tapping anywhere starts the game, the identifier can also be its button.
   - **Loading screens:** each one that isn't black (a progress bar, a tip, story text) gets `<game>/templates/common/loading/` with its `screen.png` and an `info_loading_<name>_...png`, cut by hand from a `tools.map shot` of it; mask it to its letters if the art behind changes. The lobby routine waits while one shows: nothing on a loading screen answers Back, and pressing it there is a guess.
   - **Popups:** every notice that shows between launch and the lobby (patch notes, events, news, login rewards, server messages) goes in `common/popups/<popup>/` via `tools.map popup` (map skill, "a popup"). A dialog only the lobby opens (a daily check-in, a quit prompt) is a lobby state instead, via `tools.map state`.
   - **Lobby identifier:** a pair, as in E7. One element of the scene that shows in every lobby state (day/night, HUD hidden or showing), so the routine knows it's in the lobby. One HUD element that shows only when the HUD is up, so it knows the lobby is usable. Check each scores low on the other screens (`finish` reports this), and ask whether the lobby changes with time of day or events.
   - **Many launches:** popups differ from day to day. Ask the user to launch the game a few more times (or over a few days) and add any new popup the same way, before calling the routines done.
4. **Back key.** In a menu one tap from the lobby, try `python -m core.input back` (Android Back) and see whether it closes the menu or drops the game to the Android home screen. If it drops it, try `python -m core.input back escape`. Set `BACK_KEY` in `<game>/config.py` to the key that closes menus, and rewrite the comment above it with what you found. Then press it once in the lobby: a quit prompt that opens is a lobby state (mapped with its Cancel button as a `--stay` click), and the lobby routine closes it with Cancel, never Confirm.
5. **Routines.** Write `<game>/routines/start_screen.py` and `<game>/routines/lobby.py` from E7's (`e7/routines/start_screen.py`, `e7/routines/lobby.py`), with this game's templates and dialogs, and register both in `ROUTINES`. Keep what the E7 versions do for a reason, each found the hard way:
   - check popups and lobby dialogs before trusting the lobby or start-screen match (`.claude/doc_policy.md` Rule 1): the scene can still match through a popup's dim.
   - wait out black screens (`core.nav.past_black`) and the loading screens in `common/loading/`, never press Back on them (`re1999/routines/lobby.py` has the loading wait).
   - the lobby routine hands over to `start_screen` when the start screen shows (a disconnect can lead there), and `start_screen` returns True leaving a popup open, so the lobby routine, run after it, closes it; it returns False only when it could not get past the start screen. `core.device restart` runs `start_screen` and then `lobby`, so it ends in the lobby either way.
   - a dialog closed by a tap on empty space takes the point as its close (`core.nav.dialog(info, (x, y))`), not the `btn_` crop of the background.
   - if the lobby's HUD can be at rest, wake it with `core.nav.tap_until` on a spot that is safe to tap, until the HUD element shows.
   Drop whatever only E7 needs. Log as `.claude/logging.md` says.
6. **Test**, each more than once, watching each run as `.claude/logging.md` §6 shows (the Monitor tool with that command): a failure's ERROR line names the screen it saved.
   - a cold start: `python -m core.device stop <game>`, then `python -m <game>.bot start start_screen lobby`.
   - `python -m <game>.bot lobby` from the start screen, from a menu a few taps deep, and with the quit prompt open.
   - optionally, `python -m core.device restart --fullscreen <game>`, which should end on `<game>: in lobby`. Ask first: it closes BlueStacks and every game in it.
   - the first launch of the next day, with its popups: the cold start above. Tell the user this test is still owed if it can't run yet, and name it in the notes.
   - `python -m core.tree <game>` prints no problems.
   On a failure, read the run's log and its error screen, fix, and test again.
7. **Notes.** Write a section in `<game>/notes/UI.md` for `start-screen`, `lobby` (its states and how to tell them apart) and each popup, with the scores `finish` printed and the timings seen (load times, how long the HUD stays up). Keep to what passes the delete test (`.claude/doc_policy.md` §1).
8. Close the log with `python -m core.log end`, and tell the user the game is set up: menus beyond the lobby with the map skill, routines with the task skill.
9. Commit and push. Templates stay local; check the diff for anything personal (player names, account IDs, absolute paths) before committing, since the repo is public.
