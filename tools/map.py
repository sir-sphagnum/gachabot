"""Record a mapping session as a log, then build the menu tree from it in one go.

Usage: python -m tools.map start GAME
       python -m tools.map shot
       python -m tools.map click HERE TARGET X Y W H [--fresh]
       python -m tools.map info HERE ELEMENT X Y W H
       python -m tools.map note TEXT...
       python -m tools.map log
       python -m tools.map finish

While mapping, nothing is cropped or checked: each command only captures and
appends a line to recon/map/log.jsonl, so the next click can follow at once.
`finish` then does all of it (see finish()).

start   clear recon/map/ and capture the first screen.
shot    capture a fresh screen; it becomes the current one.
click   tap the centre of box X Y W H (a button on menu HERE that opens
        TARGET), wait for the screen to settle and capture it. The box is cut
        from the current screen at finish, so it must show the button: pass
        --fresh to capture just before tapping (e.g. right after a routine).
info    log box X Y W H of the current screen as element ELEMENT of menu HERE.
note    log an observation for the game's notes, with the current screen.
log     print the log.
finish  crop every logged box into its menu folder, create new menus, check
        each image and print a report.
"""

import json
import re
import shutil
import sys
import time

import cv2
import numpy as np

from core import ROOT, templates_dir
from core.input import capture, tap
from core.vision import crop, difference, find, fingerprint, is_black
from core import tree

DIR = ROOT / "recon" / "map"
LOG = DIR / "log.jsonl"
NAME = re.compile(r"^[a-z0-9-]+$")
SETTLE_MIN, SETTLE_MAX = 1.0, 4.0  # seconds; animated menus never settle, so give up
SETTLED = 1.0  # percent of pixels changed between two captures (see core/vision.py)
GOOD = 0.95    # a crop should score at least this on the screen it came from


def settle():
    """Wait for the screen to stop changing. Returns (png, settled)."""
    time.sleep(SETTLE_MIN)
    png = capture()
    prev = _fp(png)
    deadline = time.monotonic() + SETTLE_MAX - SETTLE_MIN
    while time.monotonic() < deadline:
        time.sleep(0.3)
        png = capture()
        cur = _fp(png)
        # A loading screen is black and still, which isn't the menu yet.
        if difference(prev, cur) <= SETTLED and not is_black(cur):
            return png, True
        prev = cur
    return png, False


def _fp(png):
    return fingerprint(cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE))


def _entries():
    if not LOG.exists():
        sys.exit("No mapping session: run `python -m tools.map start GAME` first")
    return [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line]


def _append(entry):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _save(png, label):
    """Save a capture as recon/map/NN-label.png and return its repo-relative path."""
    n = len(list(DIR.glob("*.png")))
    path = DIR / f"{n:02d}-{label}.png"
    path.write_bytes(png)
    return path.relative_to(ROOT).as_posix()


def _current(entries):
    for e in reversed(entries):
        if e.get("after") or e.get("shot"):
            return e.get("after") or e["shot"]


def _check_names(*names):
    for n in names:
        if not NAME.match(n):
            sys.exit(f"'{n}': names are lowercase letters, digits and hyphens only")


def start(game):
    if not templates_dir(game).is_dir():
        sys.exit(f"No template folder {game}/templates/")
    shutil.rmtree(DIR, ignore_errors=True)
    DIR.mkdir(parents=True)
    LOG.write_text("", encoding="utf-8")
    _append({"game": game})
    path = _save(capture(), "start")
    _append({"shot": path})
    print(path)


def shot():
    _entries()
    path = _save(capture(), "shot")
    _append({"shot": path})
    print(path)


def click(here, target, box, fresh=False):
    entries = _entries()
    _check_names(here, target)
    if fresh:
        before = _save(capture(), f"before-{target}")
    else:
        before = _current(entries)
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    tx, ty = tap(cx, cy)
    png, settled = settle()
    after = _save(png, target)
    _append({"kind": "btn", "here": here, "name": target, "box": box,
             "source": before, "after": after})
    print(f"Tapped ({tx}, {ty}); {after}" + ("" if settled else " (still changing)"))


def info(here, element, box):
    entries = _entries()
    _check_names(here, element)
    source = _current(entries)
    _append({"kind": "info", "here": here, "name": element, "box": box, "source": source})
    print(f"Logged info {element} on {here} from {source}")


def note(text):
    entries = _entries()
    _append({"note": text, "screen": _current(entries)})
    print("Noted")


def finish():
    """Build the tree from the log and print a report.

    For each logged btn/info, in order:
    - HERE must be a menu in the tree, or a TARGET created earlier in the log.
    - A btn whose TARGET has no folder gets a new folder inside HERE's, with
      the click's after-capture as its screen.png. A TARGET that already exists
      is a link; its screen.png is left alone (it may be a chosen state).
    - The box is cut from the screen it was logged on, replacing any earlier
      image of the same element on that menu. If it scores below GOOD there
      in colour but matches white-only, it is saved with _white.
    - The image is then searched for, in its box, on every other menu's and
      popup's screen*.png; any match means it may not tell its menu apart.
    Notes are printed for writing into <game>/notes/.
    """
    entries = _entries()
    game = entries[0]["game"]
    menus, _ = tree.load(game)
    folders = {name: ROOT / m["path"] for name, m in menus.items()}
    notes, made = [], []
    for e in entries[1:]:
        if "note" in e:
            notes.append(e)
            continue
        if "kind" not in e:
            continue
        here, name, (x, y, w, h) = e["here"], e["name"], e["box"]
        label = f"{e['kind']} {here} -> {name}" if e["kind"] == "btn" else f"info {here}/{name}"
        if here not in folders:
            print(f"{label}: no menu '{here}' in the tree; skipped")
            continue
        d = folders[here]
        if e["kind"] == "btn":
            if name in folders:
                if name not in made:
                    print(f"{label}: '{name}' exists ({_rel(folders[name])}); "
                          f"screen.png kept, new capture is {e['after']}")
            else:
                folders[name] = d / name
                folders[name].mkdir()
                shutil.copy(ROOT / e["after"], folders[name] / "screen.png")
                made.append(name)
                print(f"{label}: new menu {_rel(folders[name])}")
        stem = f"{e['kind']}_{here}_{name}_"
        for old in d.glob(stem + "*.png"):
            old.unlink()
        out = d / f"{stem}{x}-{y}-{w}-{h}.png"
        crop(ROOT / e["source"], x, y, w, h, out)
        score = _score(find(out, ROOT / e["source"], (x, y, w, h)))
        if score < GOOD:
            white = _score(find(out, ROOT / e["source"], (x, y, w, h), white=True))
            if white >= GOOD:
                out = out.rename(out.with_name(out.stem + "_white.png"))
                score = white
        flag = "" if score >= GOOD else "  <-- crop doesn't match its source"
        print(f"  {_rel(out)}: {score:.2f} on its source{flag}")
        others = _matches_elsewhere(game, out, d)
        if others:
            print("    also matches: " + ", ".join(f"{p} ({s:.2f})" for p, s in others))
    if notes:
        print("\nNotes:")
        for n in notes:
            print(f"  - {n['note']}  [{n['screen']}]")
    menus, problems = tree.load(game)
    popups, popup_problems = tree.load_popups(game)
    print()
    tree.show(game, menus, problems + popup_problems, popups)


def _score(match):
    return match[2] if match else 0.0


def _matches_elsewhere(game, image, own):
    white = image.stem.endswith("_white")
    m = tree.ELEMENT.match(image.name)
    box = tuple(int(m[k]) for k in "xywh")
    hits = []
    for screen in sorted(templates_dir(game).rglob("screen*.png")):
        if screen.parent == own:
            continue
        match = find(image, screen, box, white=white)
        if match:
            hits.append((_rel(screen), match[2]))
    return hits


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _box(args):
    if len(args) != 4 or not all(a.isdigit() for a in args):
        sys.exit(__doc__)
    return list(map(int, args))


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    fresh = "--fresh" in args
    args = [a for a in args if a != "--fresh"]
    if cmd == "start" and len(args) == 1:
        start(args[0])
    elif cmd == "shot" and not args:
        shot()
    elif cmd == "click" and len(args) == 6:
        click(args[0], args[1], _box(args[2:]), fresh)
    elif cmd == "info" and len(args) == 6:
        info(args[0], args[1], _box(args[2:]))
    elif cmd == "note" and args:
        note(" ".join(args))
    elif cmd == "log" and not args:
        for e in _entries():
            print(json.dumps(e))
    elif cmd == "finish" and not args:
        finish()
    else:
        sys.exit(__doc__)
