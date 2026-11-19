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

Part 1 creates the files with a script. Part 2 maps the screens from launch to the lobby and writes the two routines. Run all commands from the project root. Before Part 2, read `core/notes/UI.md` (how every game's menus have behaved so far, cited below as "common: <section>") and `e7/CLAUDE.md` with its notes, the worked example.

## Part 1: the package

1. Ask the user which game, unless they said. Have them open it in BlueStacks, then find its package: `python -m core.device focus` prints the package in focus. If the game isn't installed, stop and tell them.
2. Agree on a short name: lowercase letters, digits and `_` (e.g. `e7`, `re1999`). `core.device.GAMES` may already list the game under a short name that has no folder yet; use that name, or rename its key there if the user wants another (the script refuses a package that is already listed under another name).
3. Run:
   ```
   python -m tools.new_game <game> <package> --title "<Game's Name>"
   ```
   `--title` is the name the generated files write (e.g. `"Reverse: 1999"`); without it they get the short name title-cased. It adds the `GAMES` entry, creates `<game>/` (`config.py`, `bot.py`, `routines/` with an empty `ROUTINES`, `templates/`, `notes/UI.md`, `notes/routines.md`, `CLAUDE.md`) and refuses if the folder already exists. It writes no start_screen or lobby routine: those come in Part 2.

## Part 2: from launch to the lobby

1. Open this run's log: `python -m core.log start new-game`. If it says `(inside <skill>)` and you didn't start that skill in this conversation, run `python -m core.log end --all` and start again (`.claude/logging.md` §5). Check `python -m core.device health` (common: BlueStacks memory), and again every ~30 taps. On any other failure, tell the user what it says and wait.
2. Force-stop and launch the game, so it comes up on its start screen: `python -m core.device stop <game>`, then `python -m core.device start <game>`.
3. **Start screen, popups and lobby.** Follow the map skill (`.claude/skills/map/SKILL.md`) from its Start step, with its log already open. The first screen past the loading screens is the root menu, `start-screen`. The user clicks into the game; the menu reached once the popups after START are closed becomes `lobby` (use that name, `core.nav` looks for it). Before mapping, tell the user that mapping the first launch of the day uses up its popups, so the routines can only be tested against them on the next day's first launch (step 6; common: First of the day or week). Along the way:
   - **Clicking yourself:** when the user asks Claude to set the game up alone, Claude picks each tap. Read a fresh capture before each one (`tools.map shot` when anything may have moved): a tap chosen from an old capture lands on a dialog that opened since. Read boxes off the full 1920x1080 capture or off `python -m tools.map sheet [CAPTURE...] [--box X Y W H]`, whose grid is labelled in device pixels, never off a preview you scaled yourself. `click` warns when the screen didn't change, when it still shows HERE though the click isn't `--stay`, when HERE is no menu `finish` will know, and when BlueStacks is over its memory limit: act on each before the next tap. `--auto` refuses `start-screen` (it holds "start"): log the start tap without `--auto`, since nothing is spent.
   - **Start screen identifier:** something that is always there and never changes, like E7's copyright line; a pulsing "Tap to Start" is masked (common: Moving parts). If tapping anywhere starts the game, the identifier can also be its button (common: Tap anywhere).
   - **Loading screens:** each one that isn't black (a progress bar, a tip, story text) gets `<game>/templates/common/loading/` with its `screen.png` and an `info_loading_<name>_...png`, cut by hand from a `tools.map shot` of it (common: Loading screens). Note how long launch takes to reach the start screen: it sets the lobby routine's `LAUNCH` (step 5).
   - **Start tap timing:** before writing `start_screen`, record what follows the start tap: run `python -m tools.recon recon/start --interval 0.3 --for 20` with the Bash tool's background option (never a trailing `&`: on Windows the recording outlives its shell and keeps capturing), tap, and score the start button and the start-screen identifier on the frames (`python -m tools.map score <image>... --in recon/start`); `tools.map sheet` on a few frames shows them. Note how long the button stays after a tap that took, whether it shows only after the identifier, and when the load starts: these set `start_screen`'s waits.
   - **Popups:** every notice that shows between launch and the lobby (patch notes, events, news, login rewards, server messages) goes in `common/popups/<popup>/` via `tools.map popup` (map skill, "a popup"). A dialog only the lobby opens (a daily check-in, a quit prompt) is a lobby state instead, via `tools.map state`. Identify each by its title alone: a line it shares with other popups ("Tap to continue") or one that fades in after the title makes a popup still fading in read as closed, and the routine reads the menu under it.
   - **Lobby identifier:** a pair, as in E7 (common: Lobbies). One element of the scene that shows in every lobby state (day/night, HUD hidden or showing), and one HUD element that shows only when the HUD is up. Check each scores low on the other screens (`finish` reports this), and ask whether the lobby changes with time of day or events.
   - **Mailbox:** once the lobby is mapped, find its mail button as `core/notes/dailies.md`, Mail says, and map it: `click lobby mail X Y W H --auto`, cut without the badge, then an `info` on the mailbox's title. Don't tap Claim All here: the claim is learn-dailies' step, and claiming now leaves it nothing to test until new mail arrives. A HUD that hides when idle needs the lobby routine chained before the click with `--fresh`, as in the map skill.
   - **Stamina:** find the lobby's stamina counter as `core/notes/dailies.md`, Stamina sink says. Note its name, where it shows and its max in the lobby's section of the notes: learn-dailies plans the stamina it spends from it.
   - **Many launches:** popups differ from day to day. Ask the user to launch the game a few more times (or over a few days) and add any new popup the same way, before calling the routines done.
4. **Back key.** In a menu one tap from the lobby, try `python -m core.input back` (Android Back) and see whether it closes the menu or drops the game to the Android home screen. If it drops it, try `python -m core.input back escape`. Set `BACK_KEY` in `<game>/config.py` to the key that closes menus, and rewrite the comment above it with what you found. Then press it once in the lobby: a quit prompt that opens is a lobby state, mapped with its Cancel button as a `--stay` click (common: Lobbies). Note any screen on the way where Back does nothing or only shows a toast: it's mapped as a popup or a lobby state with its own close (common: Back).
5. **Routines.** Write `<game>/routines/start_screen.py` and `<game>/routines/lobby.py` from re1999's (`re1999/routines/start_screen.py`, `re1999/routines/lobby.py`), with this game's templates and dialogs, and register both in `ROUTINES`. re1999's lobby has the loading and launch waits; E7's (`e7/routines/lobby.py`) has neither, since its loads are black, but shows how to wake a HUD at rest. Keep what they do; each is explained where it's cited:
   - popups and lobby dialogs closed before the lobby or start-screen match is trusted (`core/notes/UI.md` Rule 1).
   - each tap judged by the screen it settles on (Rule 2), START's absence held with `core.nav.held` before waiting for the lobby.
   - loads and the launch wait as common: Loading screens says, with `LAUNCH` set well above the launch time noted in step 3.
   - the screens from step 4 that Back can't close, closed by their own button (common: Back).
   - the lobby routine hands over to `start_screen` when the start screen shows (a disconnect can lead there), and `start_screen` returns True leaving a popup open, so the lobby routine, run after it, closes it; it returns False only when it could not get past the start screen. `core.device restart` runs `start_screen` and then `lobby`, so it ends in the lobby either way.
   - a HUD that can be at rest woken with `core.nav.tap_until` on a spot that is safe to tap, until the HUD element shows (common: Lobbies).
   Drop whatever only re1999 or E7 needs. Log as `.claude/logging.md` says.
6. **Test**, each more than once, watching each run as `.claude/logging.md` §6 shows (the Monitor tool with that command): a failure's ERROR line names the screen it saved.
   - a cold start: `python -m core.device stop <game>`, then `python -m <game>.bot start start_screen lobby`.
   - `python -m <game>.bot lobby` from the start screen, from a menu a few taps deep, from a menu slow to close (a 3D or map menu: a Back pressed while it closes lands on the lobby and opens quit), and with the quit prompt open.
   - optionally, `python -m core.device restart <game>`, which should end on `<game>: in lobby`. Ask first: it closes BlueStacks and every game in it.
   - the first launch of the next day, with its popups: the cold start above. Tell the user this test is still owed if it can't run yet, and name it in the notes.
   - `python -m core.tree <game>` prints no problems.
   On a failure, read the run's log and its error screen, fix, and test again. While a cold start or load runs, write the notes or the next routine instead of waiting on it.
7. **Notes.** Write a section in `<game>/notes/UI.md` for `start-screen`, `lobby` (its states and how to tell them apart, and its stamina), `mail` (where its button is, how it's identified) and each popup, with the scores `finish` printed and the timings seen (load times, how long the HUD stays up). Keep to what passes the delete test (`.claude/doc_policy.md` §1).
8. Close the log with `python -m core.log end`, and tell the user the game is set up. Its dailies come next, with the learn-dailies skill (Claude explores and proposes a plan for the user to approve); single menus can still be added with the map skill and routines with the task skill.
9. Don't commit: check the diff for anything personal (player names, account IDs, absolute paths), since the repo is public and templates stay local, then offer the commit and push at the end of the user's request (after learn-dailies, when it follows). Commit only on their yes.
