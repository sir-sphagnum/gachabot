---
name: navigate
description: Take the game to a menu that exists in its template tree (<game>/templates/), from wherever it is, by tapping down the mapped buttons. Use when the user says "go to <menu>", "navigate to <menu>", "open <menu>", "take me to <menu>", or similar.
---

# Navigate

Gets the game to a menu that the map skill has already recorded under `<game>/templates/`. `core.nav.goto` does it for any game:

1. brings the game to its lobby (the menu folder named `lobby`) with the game's lobby routine, `<game>/routines/lobby.py`, which closes popups on the way;
2. finds the shortest chain of `btn_` images from there to the target (`core.nav.route`), links included;
3. taps each button with `core.nav.tap_until` until the next menu's identifying images show (its `info_` images, or its `btn_` images if it has none), closing the game's common popups before trusting a match. Before each tap on the lobby, it runs the lobby routine again, in case the lobby hid its buttons while idle;
4. starts over from the lobby once if a step fails (e.g. a popup sent the game elsewhere).

Run all commands from the project root.

## "Go to <menu>"

1. If you haven't read anything under the game's folder this session, read `<game>/CLAUDE.md` and the notes it imports first.
2. Match the user's words to a menu folder name. `python -m core.nav <game> routes` prints every menu with its route from the lobby, without touching the game.
   - **Not in the tree**: say so and offer to map it (map skill). Don't tap around looking for it.
   - **Not reachable from the lobby** (e.g. the start screen): say so; no chain of mapped buttons leads there.
3. Open this run's log, then run it:
   ```
   python -m core.log start navigate
   ```
   It prints the log file. If it says `(inside <skill>)` and you didn't start that skill in this conversation, an earlier run never ended: run `python -m core.log end --all`, then start again (`.claude/logging.md` §5).
   ```
   python -m core.nav <game> goto <menu>
   ```
   Add `--here <current>` only when you know which menu is on screen right now (you looked at a capture since the last thing that could have changed it): it walks from there instead of going to the lobby first, and falls back to the lobby if that fails.
4. Exit 0 means the target's images matched with no popup open. Tell the user the route in one line (`lobby > sanctuary > forest-of-souls`). Take a screenshot only if they want to see it.
5. Exit 1: capture the screen (`python -m core.input screenshot recon/navigate.png`), Read it, run `python -m core.nav <game> where recon/navigate.png`, and tell the user where it stopped, using the last lines of output. An error ending in "no answer in 20s" (adb) or "blank screenshots in a row" means BlueStacks itself is stuck: run `python -m core.device health` and pass on what it says, usually to restart BlueStacks. Otherwise:
   - **a popup the bot doesn't know**: offer to map it as a common popup (map skill).
   - **a button didn't match**: the menu may have a state where it's hidden (like the lobby at rest). Ask, and note what you learn in `<game>/notes/UI.md`.
   - **the next menu didn't show though the tap landed**: its identifying images may not match this time (different lighting, art). Check with `python -m core.vision find <image> recon/navigate.png X Y W H` and tell the user the score.
   Don't retry blindly more than once.
6. Close the log once you've reported (and taken any capture step 5 calls for): `python -m core.log end`.

## A game without a lobby routine

Every game needs two things before it can be navigated:
- a menu folder named `lobby` in its template tree, the menu the game's buttons fan out from;
- `<game>/routines/lobby.py` with `run()`, which brings the game to that lobby from anywhere, with its buttons showing, and returns True once it has (see `e7/routines/lobby.py`).

## Notes

- Only click what the route needs. If a target would spend premium currency or make a purchase on arrival, ask first.
- A menu with no `btn_` leading to it from home can't be reached. If the user wants it, map the button that opens it (map skill).
