---
name: map
description: Build a navigable menu tree for the bot under <game>/templates/ while the user clicks through the game, saving each menu's screenshot, its buttons (cropped, named by where they lead) and any identifying UI elements. Use when the user says "create a path to <menu>", "map <menu>", "map the path to", or similar.
---

# Map

The user drives the game one click at a time, and you record each step as a folder tree the bot can later walk with `core.vision.find` and `core.input.tap`. Everything goes under the game's template folder, `<game>/templates/` (e.g. `e7/templates/`). Run all commands from the project root.

Mapping happens in two phases, so the user never waits on you between clicks:

1. **While mapping**, each click is one `python -m tools.map click` call: it taps, waits for the screen to settle, captures it and appends a line to `recon/map/log.jsonl`. Nothing is cropped, checked or written to notes yet.
2. **At "stop mapping"**, `python -m tools.map finish` crops every logged box into its menu folder, creates the new menus, checks each image and prints a report. You then ask for anything missing and write the notes.

## The tree

Each game is a top-level package (e.g. `e7/`) whose `templates/` folder holds all of that game's menus; `templates/` holds no images itself. Inside it, one folder per menu. A menu's folder sits inside the folder of the menu that reaches it with one tap. The game's first screen (e.g. `start-screen`) is a root menu directly in `templates/`.

```
e7/                                          <- game package
  templates/                                 <- game's template folder
    start-screen/                            <- root menu
      screen.png                             <- latest full capture of the start screen
      btn_start-screen_lobby_805-1023-311-26_white.png
      lobby/
        screen.png
        btn_lobby_summon_1620-940-180-90.png <- button on the lobby that opens summon
        info_lobby_player-level_40-20-160-50.png
        summon/
          screen.png
          btn_summon_banner-list_...png
          banner-list/
            screen.png
```

A menu folder can hold:

| File | What it is |
|---|---|
| sub-folders | menus reachable from this one with one tap. No sub-folders means this is a leaf. |
| `screen.png` | the latest full capture of this menu. For a menu with several states, this is the usable one (e.g. the lobby with its HUD showing). |
| `screen-<state>.png` | a capture of another state of the same menu (e.g. `screen-rest.png`: the lobby idle with its HUD hidden). How to tell the states apart and switch to the usable one doesn't go in the folder: write it to the game's UI notes, `<game>/notes/UI.md` (e.g. `e7/notes/UI.md`), in a section for the menu. Create the file for a new game, and a `<game>/CLAUDE.md` that imports it (`@notes/UI.md`). |
| `btn_<here>_<target>_<x>-<y>-<w>-<h>.png` | an interactable element on this menu. `<target>` is the folder it opens, or, for a button that keeps the game on this menu (claim, tab, close a dialog), the button's own name. Buttons to other menus also identify the menu they sit on when it has no `info_` images: if one is found on screen, the bot is on this menu. |
| `info_<here>_<element>_<x>-<y>-<w>-<h>.png` | an informative (non-clickable) element: used to confirm which menu the bot is on, or to read information from. |

Naming rules:
- Menu and element names are short, lowercase, hyphenated (`banner-list`, `gem-count`). Never use `_` inside a name: `_` separates fields.
- Game names are the one exception: they may use `_`, since they never appear in file names. A game's package folder must match its short name in `core.device.GAMES` (e.g. `e7`).
- Menu names are unique within a game. That is what lets a button point at a menu that lives in another branch (a link). A button whose `<target>` is no menu keeps the game where it is, so a misspelt target doesn't show up as a problem: check names when you crop.
- `<x>-<y>-<w>-<h>` is the crop box in device pixels (1920x1080): top-left corner, width, height. It is the same box `core.vision find` takes as its search location.
- Add `_white` before `.png` when the element only matches with `core.vision find --white` (semi-transparent buttons). `finish` adds it on its own when only white matching works.
- For text over a background that changes (animated art), save the template as a PNG with an alpha channel. Keep only the letters and their outline opaque: `core.vision.find` ignores transparent pixels.

The folders and file names are the whole map: there is no separate index file to keep in sync. `python -m core.tree [game]` reads the trees live (every game, or just the one named), prints them, and lists anything that doesn't fit the scheme (bad names, menus nothing opens, menus the bot can't recognise, buttons whose target has no folder). Other scripts can call `core.tree.load("<game>")` to get one game's map as a dict, and `core.tree.games()` for the list of games.

## Start: "create a path to <menu>"

1. Work out which game is running (ask if unclear). Open this run's log with `python -m core.log start map`. If it says `(inside <skill>)` and you didn't start that skill in this conversation, an earlier run never ended: run `python -m core.log end --all`, then start again (`.claude/logging.md` §5). Then run `python -m tools.map start <game>`. It clears `recon/map/` and captures the first screen; Read the path it prints.
   - If the game has no folder yet, ask what to call it, add it to `core.device.GAMES`, and create `<game>/templates/` with an empty `.gitkeep` in it (git ignores everything else under any `templates/` folder, so the `.gitkeep` is what keeps the empty folder in the repo). Then run `start`.
2. Run `python -m core.tree <game>` and find which menu this is: the folder whose `btn_*`/`info_*` images match (`python -m core.vision find <image> <capture> <x> <y> <w> <h>`, using the box in the file name).
   - If it prints `(no menus yet)`, this screen is the root. Ask the user what to call it if it isn't obvious (e.g. `start-screen`), create `<game>/templates/<root>/` and copy the capture in as `screen.png`.
   - If nothing matches, tell the user and ask which menu this is and where it belongs.
3. Tell the user which menu you are on and that you're ready for clicks. Keep track of the current menu's name for the rest of the session.

## "Click on <button>"

1. Look at the current capture: the one the last `tools.map` command printed. Run `python -m tools.map shot` first only when the screen may have changed since (the user did something, a routine ran, a timer or idle state may have kicked in).
2. Find the button the user named. If you can't find it, or more than one thing matches, ask. Do not guess.
3. Decide its box in 1920x1080 pixels: tight around the button, but including its whole label or icon. Leave out sparkles and other animated bits next to it. If the image you see is scaled, scale the box.
4. Name the target from the user's words or the button's label. If it isn't clear, use a placeholder and fix it in `recon/map/log.jsonl` once you see the new screen.
5. Tap and capture in one call:
   ```
   python -m tools.map click <here> <target> X Y W H
   ```
   It taps the box's centre, waits until two captures 0.3 s apart look the same (giving up after 4 s on animated menus) and prints the after-capture's path. When the click must follow a routine at once (e.g. the lobby falls back to rest within seconds), chain them in one command and pass `--fresh`, so the box is cut from a capture taken just before the tap:
   ```
   python -m e7.routines.lobby && python -m tools.map click lobby sanctuary 27 246 112 86 --fresh
   ```
   Only click what the user asked for. If a click would spend premium currency or make a purchase and the user did not clearly say to, ask first.
6. Read the after-capture and tell the user in one line: "tapped <button> (cx, cy) → now on <menu>". The new menu is the current one. If the screen shows:
   - **no change:** say so and ask whether to retry. The logged click will create a folder that duplicates `<here>` at finish, so remove its line from the log.
   - **a menu that exists elsewhere in the tree** (e.g. a "home" button back to the lobby): it's a link; `finish` makes no folder for it. Tell the user it's the same as `<game>/templates/<path>/`.
   - **a popup or dialog over the old menu:** ask the user which of three it is, and log the answer with `python -m tools.map note ...`:
     - a menu of its own: carry on; `finish` makes it a folder.
     - a state of the old menu: a dialog that this menu always opens on a known action (e.g. a quit prompt on Escape). At finish it becomes `screen-<state>.png` in the old menu's folder, with an `info_<here>_...png` that identifies it and a `btn_<here>_<button>_...png` for the tap that closes it (log the close with `click ... --stay`).
     - a popup: shows up over any menu, unpredictably and in the way (e.g. a reward notice, a server disconnect). At finish it goes in `<game>/templates/common/popups/<popup>/`, not the menu tree: its `screen.png`, one or more `info_<popup>_<element>_...png` that identify it (the popup counts as open only when **all** of them match), and `btn_<popup>_close_...png` for the tap that closes it. `core.nav.tap_until` closes these automatically before each tap.

## "Identify this screen by <element>"

1. Find the element on the current capture (take a `shot` first if the screen may have changed), and ask if it's ambiguous.
2. Log it: `python -m tools.map info <here> <element> X Y W H`.
3. Prefer elements that are unique to this menu and don't change (titles, fixed icons, panel frames). If the user picks something whose content changes (a counter, a timer, a player name), log it anyway, but point out that it's for reading information, not for identifying the menu.

Anything else worth keeping for the notes (a menu's states, a quirk, a timing), log with `python -m tools.map note <text>` and move on.

## Stop: "end path" / "stop mapping"

1. Run `python -m tools.map log` and check it: right menu names, no clicks that did nothing.
2. Run `python -m tools.map finish`. For each logged button and info element, it creates any new menu folder (with the after-capture as `screen.png`), crops the box from the capture it was logged on, checks the crop on that capture (adding `_white` when only white matching works) and searches for it on every other saved `screen*.png`. It leaves an existing menu's `screen.png` alone and prints the new capture's path instead. Then it prints the logged notes and the tree with its problems.
3. Go through the report:
   - a crop flagged as not matching its source: redo the box and crop it with `python -m core.vision crop`.
   - an image that also matches other screens: tell the user it can't tell its menu apart.
   - menus the bot can't recognise: ask about all of them at once, suggesting an element for each (e.g. its title). Crop the ones the user picks from the menu's `screen.png` and check them as `finish` does.
   - dialogs and popups from the notes: move their captures and crops where the click section says.
   - other problems: fix the ones you caused (bad names, misplaced files); ask about the rest.
4. Write what the session showed into `<game>/notes/UI.md`: a section for each new menu (how it's identified and what scored what), and the logged notes.
5. Close the log with `python -m core.log end`.
6. Show the user the final tree and tell them which notes changed, and give the log file `end` printed.

## Notes

- Turn off Android's Pointer location overlay before mapping. It is drawn into every screenshot and would end up baked into templates near the top of the screen.
- `recon/map/` holds only the current session; `start` wipes it. The map skill doesn't run the `recon` capture loop.
- Don't save anything under `<game>/templates/` outside the tree except its `common/` folder (popups, and `hud/` for elements shown on many menus' HUD), which `core.tree` keeps out of the menu tree.
