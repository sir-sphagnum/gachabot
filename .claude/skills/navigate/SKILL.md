---
name: navigate
description: Take the game to a menu that exists in its template tree (<game>/templates/), from wherever it is, by tapping down the mapped buttons. Use when the user says "go to <menu>", "navigate to <menu>", "open <menu>", "take me to <menu>", or similar.
---

# Navigate

Gets the game to a menu that the map skill has already recorded under `<game>/templates/`. Each game has a `<game>/nav.py` (e.g. `e7/nav.py`) that knows its home menu and wires it to `core.nav.goto`, which:

1. brings the game to the home menu (e.g. E7's active lobby, via the `lobby` routine, closing popups on the way);
2. finds the shortest chain of `btn_` images from there to the target (`core.nav.route`), links included;
3. taps each button with `core.nav.tap_until` until the next menu's identifying images show (its `info_` images, or its `btn_` images if it has none), closing the game's common popups before trusting a match;
4. starts over from home once if a step fails (e.g. a popup sent the game elsewhere).

Run all commands from the project root.

## "Go to <menu>"

1. If you haven't read anything under the game's folder this session, read `<game>/CLAUDE.md` and the notes it imports first.
2. Match the user's words to a menu folder name. `python -m <game>.nav --list` prints every menu with its route from home, without touching the game.
   - **Not in the tree**: say so and offer to map it (map skill). Don't tap around looking for it.
   - **Not reachable from home** (e.g. the start screen): say so; no chain of mapped buttons leads there.
3. Run it:
   ```
   python -m <game>.nav <menu>
   ```
   Add `--here <current>` only when you know which menu is on screen right now (you looked at a capture since the last thing that could have changed it): it walks from there instead of going home first, and falls back to home if that fails.
4. Exit 0 means the target's images matched with no popup open. Tell the user the route in one line (`lobby > sanctuary > forest-of-souls`). Take a screenshot only if they want to see it.
5. Exit 1: capture the screen (`python -m core.input screenshot recon/navigate.png`), Read it, and tell the user where it stopped, using the last lines of output. Then:
   - **a popup the bot doesn't know**: offer to map it as a common popup (map skill).
   - **a button didn't match**: the menu may have a state where it's hidden (like the lobby at rest). Ask, and note what you learn in `<game>/notes/UI.md`.
   - **the next menu didn't show though the tap landed**: its identifying images may not match this time (different lighting, art). Check with `python -m core.vision find <image> recon/navigate.png X Y W H` and tell the user the score.
   Don't retry blindly more than once.

## A game without `<game>/nav.py`

Create one modelled on `e7/nav.py`:
- `HOME`: the menu every walk starts from, the one the game's buttons fan out from (usually its lobby).
- a routine that reaches `HOME` from anywhere and returns True (write it first if the game has none; see `e7/routines/lobby.py`).
- `ready`: for menus whose buttons show only in one state, a callable that puts them in it, run before each tap on that menu.

## Notes

- Only click what the route needs. If a target would spend premium currency or make a purchase on arrival, ask first.
- A menu with no `btn_` leading to it from home can't be reached. If the user wants it, map the button that opens it (map skill).
