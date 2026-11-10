"""Show the pathfind menu trees under <game>/templates/, read live from the folders.

Usage: python -m core.tree [game]          (no game: show every game)

A game is a top-level folder with a templates/ folder (e.g. e7/templates/),
which holds that game's menus. The folders and file names are the whole map;
nothing else is stored:
  templates/<menu>/                        a root menu of the game (e.g. start-screen)
  <menu>/                                  a menu, inside the menu that opens it
  <menu>/screen.png                        latest full capture of the menu
  <menu>/screen-<state>.png                capture of another state of the menu
                                           (e.g. screen-rest.png for an idle lobby);
                                           how to recognise / switch states is kept
                                           in <game>/notes/UI.md, not here
  <menu>/btn_<menu>_<target>_<x>-<y>-<w>-<h>[_white].png
                                           a button on <menu> that opens <target>
  <menu>/info_<menu>_<element>_<x>-<y>-<w>-<h>[_white].png
                                           an element that identifies <menu> or
                                           carries information
_white means match it with core.vision.find(..., white=True). Menu names are
unique within a game, so a button whose target folder lives elsewhere is a
link to that menu.

templates/common/ is not a menu and is left out of the tree. It holds things that
can show up over any menu:
  common/popups/<popup>/                   a popup to dismiss (e.g. a reward notice)
  common/popups/<popup>/screen.png         a capture of it
  common/popups/<popup>/info_<popup>_<element>_...png
                                           identifies it: the popup is open
                                           when ALL its info_ images match
  common/popups/<popup>/btn_<popup>_close_...png
                                           the tap that closes it
"""

import re
import sys
from core import ROOT, templates_dir

ELEMENT = re.compile(
    r"^(?P<kind>btn|info)_(?P<menu>[a-z0-9-]+)_(?P<name>[a-z0-9-]+)"
    r"_(?P<x>\d+)-(?P<y>\d+)-(?P<w>\d+)-(?P<h>\d+)(?P<white>_white)?\.png$")
STATE = re.compile(r"^screen-(?P<state>[a-z0-9-]+)\.png$")
COMMON = "common"
POPUPS = "popups"


def games():
    """Names of the games: top-level folders that have a templates/ folder."""
    return sorted(p.name for p in ROOT.iterdir() if templates_dir(p.name).is_dir())


def load(game):
    """Read one game's menu tree. Returns (menus, problems).

    menus: {name: {"path", "parent", "children", "screen", "buttons", "info"}}
        "path" is relative to the repo root (e.g. "e7/templates/start-screen").
        buttons/info entries: {"file", "name", "box": (x, y, w, h), "white"}
        a button's "name" is the menu it opens.
    problems: list of strings describing anything that doesn't fit the scheme.
    """
    game_dir = templates_dir(game)
    menus, problems = {}, []
    for f in sorted(game_dir.glob("*.png")):
        problems.append(f"{_rel(f)}: images belong in a menu folder, not directly in templates/")
    common = game_dir / COMMON
    for d in sorted(p for p in game_dir.rglob("*") if p.is_dir()):
        if d == common or common in d.parents:
            continue
        rel = _rel(d)
        if d.name in menus:
            problems.append(f"menu name '{d.name}' used twice: {menus[d.name]['path']} and {rel}")
            continue
        menu = {
            "path": rel,
            "parent": d.parent.name if d.parent != game_dir else None,
            "children": sorted(c.name for c in d.iterdir() if c.is_dir()),
            "screen": d / "screen.png" if (d / "screen.png").exists() else None,
            "states": {},
            "buttons": [],
            "info": [],
        }
        _read_elements(d, rel, menu, problems)
        menus[d.name] = menu

    for name, menu in menus.items():
        targets = {b["name"] for b in menu["buttons"]}
        for child in menu["children"]:
            if child not in targets:
                problems.append(f"{menu['path']}/{child}: no button on '{name}' opens it")
        for b in menu["buttons"]:
            if b["name"] not in menus:
                problems.append(f"{menu['path']}/{b['file'].name}: target '{b['name']}' has no folder")
        if not menu["buttons"] and not menu["info"]:
            problems.append(f"{menu['path']}: no btn_/info_ images, so the bot can't recognise it")
        if not menu["screen"]:
            problems.append(f"{menu['path']}: no screen.png")
    return menus, problems


def load_popups(game):
    """Read one game's popups from <game>/templates/common/popups/. Returns (popups, problems).

    popups: {name: {"path", "screen", "states", "buttons", "info", "close"}}
        "close" is the btn_<popup>_close_ entry (None if missing).
    """
    popups, problems = {}, []
    base = templates_dir(game) / COMMON / POPUPS
    if not base.is_dir():
        return popups, problems
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        rel = _rel(d)
        popup = {"path": rel, "screen": d / "screen.png" if (d / "screen.png").exists() else None,
                 "states": {}, "buttons": [], "info": []}
        _read_elements(d, rel, popup, problems)
        popup["close"] = next((b for b in popup["buttons"] if b["name"] == "close"), None)
        if not popup["info"]:
            problems.append(f"{rel}: no info_ images, so the bot can't detect it")
        if not popup["close"]:
            problems.append(f"{rel}: no btn_{d.name}_close_ image, so the bot can't close it")
        for b in popup["buttons"]:
            if b["name"] != "close":
                problems.append(f"{rel}/{b['file'].name}: popup buttons should target 'close'")
        if not popup["screen"]:
            problems.append(f"{rel}: no screen.png")
        popups[d.name] = popup
    return popups, problems


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _read_elements(d, rel, into, problems):
    """Sort the images of folder d into into["states"], ["buttons"], ["info"]."""
    for f in sorted(d.glob("*.png")):
        if f.name == "screen.png":
            continue
        s = STATE.match(f.name)
        if s:
            into["states"][s["state"]] = f
            continue
        m = ELEMENT.match(f.name)
        if not m:
            problems.append(f"{rel}/{f.name}: name doesn't fit btn_/info_ scheme")
            continue
        if m["menu"] != d.name:
            problems.append(f"{rel}/{f.name}: says it's on '{m['menu']}' but sits in '{d.name}'")
        entry = {"file": f, "name": m["name"], "white": bool(m["white"]),
                 "box": tuple(int(m[k]) for k in "xywh")}
        into["buttons" if m["kind"] == "btn" else "info"].append(entry)


def show(game, menus, problems, popups=None):
    def box(e):
        x, y, w, h = e["box"]
        return f"({x},{y} {w}x{h}{', white' if e['white'] else ''})"

    def walk(name, depth):
        menu = menus[name]
        pad = "  " * depth
        print(f"{pad}{name}/")
        for state in menu["states"]:
            print(f"{pad}  state   {state}")
        for b in menu["buttons"]:
            target = menus.get(b["name"])
            if target is None:
                where = "  [no folder]"
            elif target["parent"] != name:
                where = f"  [link to {target['path']}]"
            else:
                where = ""
            print(f"{pad}  btn  -> {b['name']} {box(b)}{where}")
        for i in menu["info"]:
            print(f"{pad}  info    {i['name']} {box(i)}")
        for child in menu["children"]:
            if child in menus and menus[child]["parent"] == name:
                walk(child, depth + 1)

    print(f"{game}/")
    roots = [n for n, m in menus.items() if m["parent"] is None]
    if not roots:
        print("  (no menus yet)")
    for r in roots:
        walk(r, 1)
    if popups:
        print(f"  {COMMON}/{POPUPS}/")
        for name, popup in popups.items():
            print(f"    {name}/")
            for b in popup["buttons"]:
                print(f"      btn  -> {b['name']} {box(b)}")
            for i in popup["info"]:
                print(f"      info    {i['name']} {box(i)}")
    if problems:
        print("\nProblems:")
        for p in problems:
            print(f"  - {p}")


if __name__ == "__main__":
    names = sys.argv[1:] or games()
    if not names:
        print("(no games yet)")
    for i, game in enumerate(names):
        if not templates_dir(game).is_dir():
            sys.exit(f"No template folder {game}/templates/")
        if i:
            print()
        menus, problems = load(game)
        popups, popup_problems = load_popups(game)
        show(game, menus, problems + popup_problems, popups)
