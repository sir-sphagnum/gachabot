"""Record a mapping session as a log, then build the menu tree from it in one go.

Usage: python -m tools.map start GAME
       python -m tools.map shot
       python -m tools.map click HERE TARGET X Y W H [--fresh] [--stay]
       python -m tools.map info HERE ELEMENT X Y W H [--on CAPTURE]
       python -m tools.map leads MENU [--after CAPTURE]
       python -m tools.map note TEXT...
       python -m tools.map log
       python -m tools.map finish
       python -m tools.map rename OLD NEW

While mapping, nothing is cropped or checked: each command only captures and
appends a line to recon/map/log.jsonl, so the next click can follow at once.
`finish` then does all of it (see finish()).

start   clear recon/map/ and capture the first screen.
shot    capture a fresh screen; it becomes the current one.
click   tap the centre of box X Y W H (a button on menu HERE that opens
        TARGET), wait for the screen to settle and capture it. The box is cut
        from the current screen at finish, so it must show the button: pass
        --fresh to capture just before tapping (e.g. right after a routine).
        --stay: the button keeps the game on HERE (claim, tab, close a dialog);
        TARGET names the button itself and finish makes no menu for it.
info    log box X Y W H of the current screen as element ELEMENT of menu HERE.
        --on: cut it from that capture in recon/map/ instead (e.g. the one a
        menu was reached on, when it isn't the last).
leads   mark the last click as opening menu MENU (drops --stay, renames its
        target). --after: that capture is the menu's screen, for a menu that
        only showed on a later `shot` (a load after the tap).
note    log an observation for the game's notes, with the current screen.
log     print the log, then the new menus nothing logged identifies yet.
finish  crop every logged box into its menu folder, create new menus, check
        each image and print a report.
rename  rename menu OLD to NEW in the session's game: its folder, the images
        named after it (its own and the buttons that open it) and the log.
CAPTURE is a file name in recon/map/ (e.g. 04-shot.png).
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path

import cv2

from core import ROOT, templates_dir
from core.input import capture, tap
from core.log import logger, setup
from core.vision import crop, difference, find, fingerprint, is_black, save
from core import tree
from core.nav import locate

log = logger(__file__)

DIR = ROOT / "recon" / "map"
LOG = DIR / "log.jsonl"
NAME = re.compile(r"^[a-z0-9-]+$")
SETTLE_MIN, SETTLE_MAX = 1.0, 4.0  # seconds; animated menus never settle, so give up
SETTLED = 1.0  # percent of pixels changed between two captures (see core/vision.py)
GOOD = 0.95    # a crop should score at least this on the screen it came from
THRESHOLD = 0.85  # core.vision.find's default: at or above it, an image matches


def settle():
    """Wait for the screen to stop changing. Returns (capture, settled)."""
    time.sleep(SETTLE_MIN)
    img = capture()
    prev = _fp(img)
    deadline = time.monotonic() + SETTLE_MAX - SETTLE_MIN
    while time.monotonic() < deadline:
        time.sleep(0.3)
        img = capture()
        cur = _fp(img)
        # A loading screen is black and still, which isn't the menu yet.
        if difference(prev, cur) <= SETTLED and not is_black(cur):
            return img, True
        prev = cur
    return img, False


def _fp(img):
    return fingerprint(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))


def _entries():
    if not LOG.exists():
        sys.exit("No mapping session: run `python -m tools.map start GAME` first")
    # utf-8-sig: a log edited by hand in PowerShell gains a byte-order mark.
    return [json.loads(line) for line in LOG.read_text(encoding="utf-8-sig").splitlines() if line]


def _append(entry):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _save(img, label):
    """Save a capture as recon/map/NN-label.png and return its repo-relative path."""
    n = len(list(DIR.glob("*.png")))
    path = DIR / f"{n:02d}-{label}.png"
    save(img, path)
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
    log.info(f"started {game}, {path}")
    print(path)


def shot():
    _entries()
    path = _save(capture(), "shot")
    _append({"shot": path})
    log.debug(f"shot {path}")
    print(path)


def click(here, target, box, fresh=False, stay=False):
    entries = _entries()
    _check_names(here, target)
    if fresh:
        before = _save(capture(), f"before-{target}")
    else:
        before = _current(entries)
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    tx, ty = tap(cx, cy)
    img, settled = settle()
    after = _save(img, target)
    entry = {"kind": "btn", "here": here, "name": target, "box": box,
             "source": before, "after": after}
    if stay:
        entry["stay"] = True
    _append(entry)
    still = "" if settled else " (still changing)"
    log.info(f"{here} {'/' if stay else '>'} {target} at ({tx}, {ty}), {after}{still}")
    print(f"Tapped ({tx}, {ty}); {after}{still}")


def info(here, element, box, on=None):
    entries = _entries()
    _check_names(here, element)
    source = _capture_path(on) if on else _current(entries)
    _append({"kind": "info", "here": here, "name": element, "box": box, "source": source})
    log.info(f"info {here}/{element} {box} on {source}")
    print(f"Logged info {element} on {here} from {source}")


def leads(menu, after=None):
    """Mark the last click as opening `menu`: it loses --stay, takes `menu` as
    its target, and, with `after`, that capture as the menu's screen (for a
    menu that showed only on a later `shot`)."""
    entries = _entries()
    _check_names(menu)
    clicks = [e for e in entries if e.get("kind") == "btn"]
    if not clicks:
        sys.exit("No click logged yet")
    e = clicks[-1]
    e.pop("stay", None)
    old, e["name"] = e["name"], menu
    if after:
        e["after"] = _capture_path(after)
    _write(entries)
    log.info(f"{e['here']} > {menu} (was {old}), {e['after']}")
    print(json.dumps(e))


def rename(old, new):
    """Rename menu `old` to `new`: its folder, every image named after it (its
    own, and buttons on other menus that open it), and the log's lines."""
    _check_names(new)
    game = _entries()[0]["game"]
    menus, _ = tree.load(game)
    if old not in menus:
        sys.exit(f"No menu '{old}'")
    if new in menus:
        sys.exit(f"Menu '{new}' already exists")
    moves = []
    for d in templates_dir(game).rglob("*.png"):
        m = tree.ELEMENT.match(d.name)
        if m and old in (m["menu"], m["name"]):
            here = new if m["menu"] == old else m["menu"]
            name = new if m["name"] == old and m["kind"] == "btn" else m["name"]
            moves.append((d, d.with_name(d.name.replace(f"{m['kind']}_{m['menu']}_{m['name']}_",
                                                        f"{m['kind']}_{here}_{name}_", 1))))
    for a, b in moves:
        a.rename(b)
        print(f"{_rel(a)} -> {b.name}")
    folder = ROOT / menus[old]["path"]
    folder.rename(folder.with_name(new))
    print(f"{_rel(folder)} -> {new}/")
    entries = _entries()
    for e in entries:
        if "kind" in e:
            e["here"] = new if e["here"] == old else e["here"]
            if e["name"] == old and (e["kind"] == "btn" and not e.get("stay")):
                e["name"] = new
    _write(entries)
    log.info(f"renamed menu {old} to {new}, {len(moves)} images")


def _capture_path(name):
    """Repo-relative path of a capture in recon/map/, given its file name or path."""
    path = DIR / Path(name).name
    if not path.exists():
        sys.exit(f"No capture {path.name} in {_rel(DIR)}/")
    return _rel(path)


def _write(entries):
    LOG.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")


def note(text):
    entries = _entries()
    _append({"note": text, "screen": _current(entries)})
    log.info(f"note: {text}")
    print("Noted")


def finish():
    """Build the tree from the log and print a report.

    For each logged btn/info, in order:
    - HERE must be a menu in the tree, or a TARGET created earlier in the log.
    - A btn logged with --stay is cropped on HERE and makes no menu.
    - Any other btn whose TARGET has no folder gets a new folder inside HERE's, with
      the click's after-capture as its screen.png. A TARGET that already exists
      is a link; its screen.png is left alone (it may be a chosen state).
    - The box is cut from the screen it was logged on, replacing any earlier
      image of the same element on that menu. If it scores below GOOD there
      in colour but matches white-only, it is saved with _white.
    - The image is then scored, in its box, on every other menu's and popup's
      screen*.png. The best score is printed (the "at most X elsewhere" the
      notes cite); any match means it may not tell its menu apart.
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
            log.warning(f"{label}: no menu {here} in the tree, skipping")
            continue
        d = folders[here]
        if e["kind"] == "btn" and not e.get("stay"):
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
                log.info(f"new menu {_rel(folders[name])}")
        stem = f"{e['kind']}_{here}_{name}_"
        anywhere = ""  # a recrop keeps _anywhere, which only a rename adds
        for old in d.glob(stem + "*.png"):
            m = tree.ELEMENT.match(old.name)
            if m and m["anywhere"]:
                anywhere = "_anywhere"
            old.unlink()
        out = d / f"{stem}{x}-{y}-{w}-{h}{anywhere}.png"
        crop(ROOT / e["source"], x, y, w, h, out)
        score = _score(find(out, ROOT / e["source"], (x, y, w, h)))
        if score < GOOD:
            white = _score(find(out, ROOT / e["source"], (x, y, w, h), white=True))
            if white >= GOOD:
                out = out.rename(out.with_name(out.stem + "_white.png"))
                score = white
        flag = "" if score >= GOOD else "  <-- crop doesn't match its source"
        print(f"  {_rel(out)}: {score:.2f} on its source{flag}")
        (log.debug if score >= GOOD else log.warning)(f"{out.name}: {score:.2f} on its source")
        scores = _scores_elsewhere(game, out, d)
        if scores:
            print(f"    at most {scores[0][1]:.2f} elsewhere ({scores[0][0]})")
        others = [(p, s) for p, s in scores if s >= THRESHOLD]
        if others:
            print("    also matches: " + ", ".join(f"{p} ({s:.2f})" for p, s in others))
            log.warning(f"{out.name} also matches " + ", ".join(f"{p} ({s:.2f})" for p, s in others))
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


def _scores_elsewhere(game, image, own):
    """(screen, score) for every saved screen outside menu folder `own`, best first."""
    scores = []
    for screen in sorted(templates_dir(game).rglob("screen*.png")):
        if screen.parent == own:
            continue
        scores.append((_rel(screen), _score(locate(image, screen, threshold=0.0))))
    return sorted(scores, key=lambda s: -s[1])


def unidentified(entries):
    """Menus this log creates that nothing logged identifies yet: no info_ on
    them and no button from them to another menu."""
    menus, _ = tree.load(entries[0]["game"])
    new = [e["name"] for e in entries if e.get("kind") == "btn" and not e.get("stay")
           and e["name"] not in menus]
    marked = {e["here"] for e in entries
              if e.get("kind") == "info" or (e.get("kind") == "btn" and not e.get("stay"))}
    return [m for m in dict.fromkeys(new) if m not in marked]


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _box(args):
    if len(args) != 4 or not all(a.isdigit() for a in args):
        sys.exit(__doc__)
    return list(map(int, args))


if __name__ == "__main__":
    setup(console=False)
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    fresh, stay = "--fresh" in args, "--stay" in args
    args = [a for a in args if a not in ("--fresh", "--stay")]
    opts = {}
    for flag in ("--on", "--after"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(__doc__)
            opts[flag] = args[i + 1]
            del args[i:i + 2]
    if cmd == "start" and len(args) == 1:
        start(args[0])
    elif cmd == "shot" and not args:
        shot()
    elif cmd == "click" and len(args) == 6:
        click(args[0], args[1], _box(args[2:]), fresh, stay)
    elif cmd == "info" and len(args) == 6:
        info(args[0], args[1], _box(args[2:]), opts.get("--on"))
    elif cmd == "leads" and len(args) == 1:
        leads(args[0], opts.get("--after"))
    elif cmd == "rename" and len(args) == 2:
        rename(*args)
    elif cmd == "note" and args:
        note(" ".join(args))
    elif cmd == "log" and not args:
        entries = _entries()
        for e in entries:
            print(json.dumps(e))
        missing = unidentified(entries)
        if missing:
            print("No identifier yet: " + ", ".join(missing))
    elif cmd == "finish" and not args:
        finish()
    else:
        sys.exit(__doc__)
