---
name: map
description: Build a navigable menu tree for the bot under <game>/templates/ while the user clicks through the game, saving each menu's screenshot, its buttons (cropped, named by where they lead) and any identifying UI elements. Use when the user says "create a path to <menu>", "map <menu>", "map the path to", or similar.
---

# Map

Builds on the `recon` skill: the user drives the game one click at a time, and you record each step as a folder tree the bot can later walk with `core.vision.find` and `core.input.tap`. Everything goes under the game's template folder, `<game>/templates/` (e.g. `e7/templates/`). Run all commands from the project root.

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
| `screen.png` | the latest full capture of this menu. Overwrite it whenever the menu is revisited. For a menu with several states, this is the usable one (e.g. the lobby with its HUD showing). |
| `screen-<state>.png` | a capture of another state of the same menu (e.g. `screen-rest.png`: the lobby idle with its HUD hidden). How to tell the states apart and switch to the usable one doesn't go in the folder: write it to the game's UI notes, `<game>/notes/UI.md` (e.g. `e7/notes/UI.md`), in a section for the menu. Create the file for a new game, and a `<game>/CLAUDE.md` that imports it (`@notes/UI.md`). |
| `btn_<here>_<target>_<x>-<y>-<w>-<h>.png` | an interactable element on this menu. `<target>` is the folder it opens. Buttons also identify the menu they sit on: if one is found on screen, the bot is on this menu. |
| `info_<here>_<element>_<x>-<y>-<w>-<h>.png` | an informative (non-clickable) element: used to confirm which menu the bot is on, or to read information from. |

Naming rules:
- Menu and element names are short, lowercase, hyphenated (`banner-list`, `gem-count`). Never use `_` inside a name: `_` separates fields.
- Game names are the one exception: they may use `_`, since they never appear in file names. A game's package folder must match its short name in `core.device.GAMES` (e.g. `e7`).
- Menu names are unique within a game. That is what lets a button point at a menu that lives in another branch (see "Menu already exists" below).
- `<x>-<y>-<w>-<h>` is the crop box in device pixels (1920x1080): top-left corner, width, height. It is the same box `core.vision find` takes as its search location.
- Add `_white` before `.png` when the element only matches with `core.vision find --white` (semi-transparent buttons).
- For text over a background that changes (animated art), save the template as a PNG with an alpha channel. Keep only the letters and their outline opaque: `core.vision.find` ignores transparent pixels. See `e7/notes/UI.md`, start-screen.

The folders and file names are the whole map: there is no separate index file to keep in sync. `python -m core.tree [game]` reads the trees live (every game, or just the one named), prints them, and lists anything that doesn't fit the scheme (bad names, menus nothing opens, menus the bot can't recognise, buttons whose target has no folder). Other scripts can call `core.tree.load("<game>")` to get one game's map as a dict, and `core.tree.games()` for the list of games.

## Start: "create a path to <menu>"

1. Start recon as the `recon` skill describes (`python -m tools.recon` in the background).
2. Take a screenshot (`python -m core.input screenshot recon/current.png`) and Read it.
3. Work out which game is running (ask if unclear) and run `python -m core.tree <game>` to see its tree, then work out where you are:
   - If the game has no folder yet, ask what to call it, add it to `core.device.GAMES`, and create `<game>/templates/` with an empty `.gitkeep` in it (git ignores everything else under any `templates/` folder, so the `.gitkeep` is what keeps the empty folder in the repo).
   - If it prints `(no menus yet)`, this screen is the root. Ask the user what to call it if it isn't obvious (e.g. `start-screen`), create `<game>/templates/<root>/` and copy the screenshot in as `screen.png`.
   - If a tree exists, find the folder whose `btn_*`/`info_*` images match the current screen (`python -m core.vision find <image> recon/current.png <x> <y> <w> <h>`, using the box in the file name). That folder is the current menu. If nothing matches, tell the user and ask which menu this is and where it belongs.
4. Tell the user which menu you are on and that you're ready for clicks. Keep track of the current menu folder for the rest of the session.

## "Click on <button>"

1. Take a fresh screenshot and Read it. Find the button the user named. If you can't find it, or more than one thing matches, ask. Do not guess.
2. Decide the button's crop box in 1920x1080 pixels: tight around the button, but including its whole label or icon. If the image you see is scaled, scale the box to 1920x1080.
3. Ask the user, or infer from their words, what the button leads to, so you can name the target. If it isn't clear before clicking, click first and name it from the new screen.
4. Crop the button from the **before-click** screenshot into the current menu's folder:
   ```
   python -m core.vision crop recon/current.png X Y W H <game>/templates/<path>/btn_<here>_<target>_X-Y-W-H.png
   ```
5. Check the crop matches where it came from:
   ```
   python -m core.vision find <game>/templates/<path>/btn_<here>_<target>_X-Y-W-H.png recon/current.png X Y W H
   ```
   It should return the button's centre with a score near 1.0. If it returns `None`, the crop is wrong; redo it. If the button is semi-transparent (background shows through), also try `--white`; if only `--white` matches well, rename the file with the `_white` suffix.
6. Tap the centre of the box (`python -m core.input tap CX CY`), following the recon skill's rules (only what the user asked; ask before anything that spends premium currency or purchases).
7. Wait for the screen to settle: take screenshots about 1 second apart until two in a row look the same (no loading spinner, transition or animation in progress), then Read the last one.
8. Handle the result:
   - **Screen didn't change:** tell the user, delete nothing, and don't create a folder. Ask whether to retry.
   - **New menu:** create `<game>/templates/<path>/<target>/`, save the settled screenshot there as `screen.png`, and make it the current menu. If you named the target after clicking, rename the button file to use it.
   - **Menu already exists elsewhere in the tree** (its buttons/info elements match, e.g. a "home" button back to the lobby): don't make a folder. The button file already names that menu as its target, so it is a link; `core.tree` shows it as `[link to <game>/templates/<path>]`. Refresh that menu's `screen.png`, make it the current menu, and tell the user it's the same as `<game>/templates/<other path>/`.
   - **Popup or dialog over the old menu:** ask the user which of three it is:
     - a menu of its own: gets a folder;
     - a state of the old menu: a dialog that this menu always opens on a known action (e.g. a quit prompt on Escape). Save it in the old menu's folder as `screen-<state>.png`, with an `info_<here>_...png` that identifies it and a `btn_<here>_<here>_...png` for the tap that closes it, and describe the state in the game's UI notes;
     - a popup: shows up over any menu, unpredictably and in the way (e.g. a reward notice, a server disconnect). It goes in `<game>/templates/common/popups/<popup>/`, not the menu tree: save its `screen.png`, one or more `info_<popup>_<element>_...png` that identify it (the popup counts as open only when **all** of them match), and `btn_<popup>_close_...png` for the tap that closes it. `core.nav.tap_until` closes these automatically before each tap.
9. Tell the user in a line: what you clicked (name, box), the file you saved, and which menu folder you are now in.

## "Identify this screen by <element>"

1. Take a fresh screenshot of the current menu, find the element, and ask if it's ambiguous.
2. Crop it into the current menu's folder as `info_<here>_<element>_X-Y-W-H.png`, then check it with `core.vision find` the same way as a button.
3. Prefer elements that are unique to this menu and don't change (titles, fixed icons, panel frames). If the user picks something whose content changes (a counter, a timer, a player name), save it anyway, but point out that it's for reading information, not for identifying the menu.

## Stop: "end path" / "stop mapping"

1. Stop recon as the `recon` skill describes.
2. Run `python -m core.tree` and show the user the tree and any problems it lists. Fix the ones you caused (bad names, misplaced files); ask about the rest.

## Notes

- Turn off Android's Pointer location overlay before cropping. It is drawn into every screenshot and would end up baked into templates near the top of the screen.
- Re-cropping a button that already exists: overwrite the file if the box is the same; if the box changed, delete the old file so there's only one per button.
- Don't save anything under `<game>/templates/` outside the tree except its `common/` folder (popups), which `core.tree` keeps out of the menu tree.
