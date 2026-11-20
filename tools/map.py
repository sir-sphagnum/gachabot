"""Record a mapping session as a log, then build the menu tree from it in one go.

Usage: python -m tools.map start GAME
       python -m tools.map shot
       python -m tools.map click HERE TARGET X Y W H [--fresh] [--stay] [--auto] [--moving]
       python -m tools.map back
       python -m tools.map info HERE ELEMENT X Y W H [--on CAPTURE]
       python -m tools.map leads MENU [--after CAPTURE]
       python -m tools.map popup NAME [--on CAPTURE]
       python -m tools.map state MENU STATE [--on CAPTURE]
       python -m tools.map note TEXT...
       python -m tools.map log
       python -m tools.map finish
       python -m tools.map score [MENU|IMAGE...] [--in FOLDER]
       python -m tools.map sheet [CAPTURE...] [--box X Y W H]
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
        Without --fresh it first refuses to tap, and makes a fresh capture the
        current screen, when the box no longer looks as it does on the current
        one (a list still moving, a swipe made outside tools.map).
        --moving skips that check, for a control that animates in place.
        --stay: the button keeps the game on HERE (claim, tab, close a dialog);
        TARGET names the button itself and finish makes no menu for it.
        --auto: Claude chose this tap itself (learn-dailies), not the user.
        Refused when TARGET or HERE has a word that can spend
        (core.tree.SPEND_WORDS); such taps run without --auto, once the user
        or learn-dailies' plan allows the spend. The log line keeps "auto", so the steps Claude chose
        can be told from the user's.
        After the tap it warns (printed and logged) when HERE is no menu finish
        will know (not in the tree, not logged as a popup or opened by an
        earlier click), when the screen didn't change, when it still shows
        HERE's identifier though the click isn't --stay (a tab, claim or
        dialog: log it --stay, and a dialog also as a state), and when
        BlueStacks is over its memory limit (core.device.health).
back    press the game's BACK_KEY (<game>/config.py), wait for the screen to
        settle and capture it; it becomes the current one. For coming back
        from a menu opened while exploring.
info    log box X Y W H of the current screen as element ELEMENT of menu HERE.
        --on: cut it from that capture in recon/map/ instead (e.g. the one a
        menu was reached on, when it isn't the last).
leads   mark the last click as opening menu MENU (drops --stay, renames its
        target). --after: that capture is the menu's screen, for a menu that
        only showed on a later `shot` (a load after the tap).
popup   mark the current screen (or --on CAPTURE) as showing popup NAME:
        finish creates common/popups/NAME/ from it and crops the info and
        close lines logged on NAME there.
state   mark the current screen (or --on CAPTURE) as state STATE of MENU (a
        dialog the menu opens). finish saves it as MENU's screen-STATE.png.
note    log an observation for the game's notes, with the current screen.
log     print the log, then the menus it touches that nothing identifies yet
        (new ones, and existing ones with no info_ or button to another menu).
finish  crop every logged box into its menu folder, create new menus, check
        each image and print a report. A button tapped several times on the
        same box is cropped once, from its first tap.
score   score images on every capture of this session and every saved screen:
        the images of the menus the log touches, or of the MENUs or IMAGE
        paths given. --in: score them on the PNGs in FOLDER instead of this
        session's captures (a tools.recon recording, a probe's frames); with
        IMAGE paths only it needs no mapping session.
sheet   save recon/sheet.png: the CAPTUREs (default: the session's last 8),
        4 to a row, each with its file name and a grid labelled in device
        pixels (1920x1080), so a box can be read off a preview without
        scaling by hand. --box: show only that part of each capture, larger.
        CAPTURE is a file name in recon/map/ or any PNG path.
rename  rename menu OLD to NEW in the session's game: its folder, the images
        named after it (its own and the buttons that open it) and the log.
CAPTURE is a file name in recon/map/ (e.g. 04-shot.png).
"""

import hashlib
import importlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

import cv2

from core import ROOT, templates_dir
from core.input import back as press_back, capture, tap
from core.log import logger, setup
from core.vision import crop, diff, difference, find, fingerprint, is_black, save
from core import tree
from core.device import health as device_health
from core.nav import identity as nav_identity, locate

log = logger(__file__)

DIR = ROOT / "recon" / "map"
LOG = DIR / "log.jsonl"
CUT = DIR / "cut.json"  # hashes of the images finish wrote this session
NAME = re.compile(r"^[a-z0-9-]+$")
SETTLE_MIN, SETTLE_MAX = 1.0, 4.0  # seconds; animated menus never settle, so give up
SETTLED = 1.0  # percent of pixels changed between two captures (see core/vision.py)
GOOD = 0.95    # a crop should score at least this on the screen it came from
THRESHOLD = 0.85  # core.vision.find's default: at or above it, an image matches
# Mean pixel difference (core.vision.diff) above which a box has changed. e7
# measured 0.0-0.1 on still icons between captures, 5.9 and up on a counter
# that changed by one digit.
MOVED = 3.0


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
    _append({"game": game, "started": time.time()})
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


def click(here, target, box, fresh=False, stay=False, auto=False, moving=False):
    entries = _entries()
    _check_names(here, target)
    if auto and (tree.spends(target) or tree.spends(here)):
        sys.exit(f"'{here} > {target}' may spend something (core.tree.SPEND_WORDS): "
                 "ask the user, then click without --auto")
    if fresh:
        before = _save(capture(), f"before-{target}")
    else:
        before = _current(entries)
        if not moving:
            _same_box(before, box)
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    tx, ty = tap(cx, cy)
    img, settled = settle()
    after = _save(img, target)
    entry = {"kind": "btn", "here": here, "name": target, "box": box,
             "source": before, "after": after}
    if stay:
        entry["stay"] = True
    if auto:
        entry["auto"] = True
    if moving:
        entry["moving"] = True
    _append(entry)
    still = "" if settled else " (still changing)"
    log.info(f"{here} {'/' if stay else '>'} {target} at ({tx}, {ty}), {after}{still}")
    print(f"Tapped ({tx}, {ty}); {after}{still}")
    _warn_click(entries, here, stay, ROOT / before, img)


def _same_box(before, box):
    """Exit without tapping when the screen in `box` no longer looks as it does
    on capture `before`, the one the box was read from: a tap chosen there
    would land on whatever moved in since (a list still gliding, a swipe made
    outside tools.map), and finish would cut the box from a capture that
    doesn't show the button. The fresh capture becomes the current one."""
    now = capture()
    moved = diff(ROOT / before, now, box)
    if moved <= MOVED:
        return
    path = _save(now, "shot")
    _append({"shot": path})
    log.warning(f"box {box} changed since {Path(before).name} ({moved:.1f}), not tapping")
    sys.exit(f"The screen in box {' '.join(map(str, box))} changed since {before} "
             f"(mean difference {moved:.1f}): not tapped. Read {path} and choose the box again "
             "(--moving for a control that animates in place)")


def _warn(text):
    print(f"  warning: {text}")
    log.warning(text)


def _warn_click(entries, here, stay, before, after):
    """Print the warnings click() promises (see the module docstring)."""
    menus, _ = tree.load(entries[0]["game"])
    if not _known(entries, menus, here):
        _warn(f"no menu '{here}' in the tree or opened earlier in the log: finish will skip this line")
    elif before.exists() and difference(_fp(cv2.imread(str(before))), _fp(after)) <= SETTLED:
        _warn("the screen didn't change: remove this line from the log, or tap again")
    elif not stay and here in menus and any(locate(t, after) for t in nav_identity(menus, here)):
        _warn(f"the screen still shows {here} (its identifier matches): if the tap kept the game there "
              "(a tab, a claim, a dialog), log it --stay (a dialog also as a state)")
    ok, message = device_health()
    if not ok:
        _warn(message)


def _known(entries, menus, name):
    """True when finish will have a folder for menu or popup `name`."""
    if name in menus or name in tree.load_popups(entries[0]["game"])[0]:
        return True
    return any(e.get("popup") == name or (e.get("kind") == "btn" and not e.get("stay")
                                         and e["name"] == name) for e in entries)


def back():
    entries = _entries()
    game = entries[0]["game"]
    key = importlib.import_module(f"{game}.config").BACK_KEY
    press_back(key)
    img, settled = settle()
    path = _save(img, "back")
    _append({"shot": path, "back": key})
    still = "" if settled else " (still changing)"
    log.info(f"back ({key}), {path}{still}")
    print(f"Pressed {key}; {path}{still}")


def info(here, element, box, on=None):
    entries = _entries()
    _check_names(here, element)
    source = _capture_path(on) if on else _current(entries)
    _append({"kind": "info", "here": here, "name": element, "box": box, "source": source})
    log.info(f"info {here}/{element} {box} on {source}")
    print(f"Logged info {element} on {here} from {source}")
    if not _known(entries, tree.load(entries[0]["game"])[0], here):
        _warn(f"no menu '{here}' in the tree or opened earlier in the log: finish will skip this line")


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


def popup(name, on=None):
    """Mark the current capture (or `on`) as showing popup `name`. At finish it
    becomes <game>/templates/common/popups/<name>/, with that capture as its
    screen.png, and info/btn lines logged on `name` are cropped there."""
    entries = _entries()
    _check_names(name)
    screen = _capture_path(on) if on else _current(entries)
    _append({"popup": name, "screen": screen})
    log.info(f"popup {name} on {screen}")
    print(f"Logged popup {name} on {screen}")


def state(menu, name, on=None):
    """Mark the current capture (or `on`) as state `name` of menu `menu`. At
    finish it is saved as screen-<name>.png in the menu's folder."""
    entries = _entries()
    _check_names(menu, name)
    screen = _capture_path(on) if on else _current(entries)
    _append({"state": name, "menu": menu, "screen": screen})
    log.info(f"state {menu}/{name} on {screen}")
    print(f"Logged state {name} of {menu} on {screen}")


def note(text):
    entries = _entries()
    _append({"note": text, "screen": _current(entries)})
    log.info(f"note: {text}")
    print("Noted")


def finish():
    """Build the tree from the log and print a report.

    First, each logged popup gets common/popups/NAME/ with its capture as
    screen.png (kept if the popup exists). Then, for each logged line, in order:
    - state: copies the capture to MENU's screen-STATE.png.
    - btn/info: HERE must be a menu in the tree, a TARGET created earlier in
      the log, or a popup (existing or logged).
    - A btn logged with --stay is cropped on HERE and makes no menu.
    - Any other btn whose TARGET has no folder gets a new folder inside HERE's, with
      the click's after-capture as its screen.png. A TARGET that already exists
      is a link; its screen.png is left alone (it may be a chosen state).
    - The box is cut from the screen it was logged on, replacing any earlier
      image of the same element on that menu, unless that image was changed
      by hand after the session started (_by_hand): then it is kept and the
      line skipped. If it scores below GOOD there
      in colour but matches white-only, it is saved with _white.
    - The image is then scored, in its box, on every other menu's and popup's
      screen*.png. The best score is printed (the "at most X elsewhere" the
      notes cite); any match means it may not tell its menu apart.
    Notes are printed for writing into <game>/notes/.
    """
    entries = _entries()
    game = entries[0]["game"]
    started = entries[0].get("started")
    cut = set(json.loads(CUT.read_text(encoding="utf-8"))) if CUT.exists() else set()
    menus, _ = tree.load(game)
    folders = {name: ROOT / m["path"] for name, m in menus.items()}
    for name, p in tree.load_popups(game)[0].items():
        folders.setdefault(name, ROOT / p["path"])
    # Popups first, so their info/close lines find them wherever the popup
    # line sits in the log (it can be logged late, with --on).
    for e in entries[1:]:
        if "popup" in e:
            _make_popup(game, e, folders)
    notes, made = [], []
    taps = {}
    for e in entries[1:]:
        if "kind" in e:
            taps[_key(e)] = taps.get(_key(e), 0) + 1
    done = set()
    for e in entries[1:]:
        if "note" in e:
            notes.append(e)
            continue
        if "popup" in e:
            continue
        if "state" in e:
            if e["menu"] not in folders:
                print(f"state {e['menu']}/{e['state']}: no menu '{e['menu']}' in the tree; skipped")
                log.warning(f"state {e['menu']}/{e['state']}: no menu {e['menu']} in the tree, skipping")
                continue
            out = folders[e["menu"]] / f"screen-{e['state']}.png"
            shutil.copy(ROOT / e["screen"], out)
            print(f"state {e['menu']}/{e['state']}: {_rel(out)}")
            log.info(f"state {_rel(out)}")
            continue
        if "kind" not in e:
            continue
        # A repeated tap on the same box (a +1 pressed five times) is cropped
        # once, from its first capture: each recrop would only replace the last.
        if _key(e) in done:
            continue
        done.add(_key(e))
        here, name, (x, y, w, h) = e["here"], e["name"], e["box"]
        label = f"{e['kind']} {here} -> {name}" if e["kind"] == "btn" else f"info {here}/{name}"
        if taps[_key(e)] > 1:
            label += f" (logged {taps[_key(e)]} times)"
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
        olds = list(d.glob(stem + "*.png"))
        edited = [old for old in olds if _by_hand(old, started, cut)]
        if edited:
            print(f"{label}: kept {_rel(edited[0])}, changed by hand since this session started; "
                  "to cut it from the log instead, delete it and run finish again")
            log.warning(f"{edited[0].name}: changed by hand since the session started, keeping it")
            continue
        anywhere = ""  # a recrop keeps _anywhere, which only a rename adds
        for old in olds:
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
        # Saved after each crop, not at the end: a finish that crashes part
        # way would otherwise leave its own crops looking hand-made.
        cut.add(_hash(out))
        CUT.write_text(json.dumps(sorted(cut)), encoding="utf-8")
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


def _make_popup(game, e, folders):
    """Create popup e["popup"]'s folder (first time it's logged) and add it to
    `folders`, so the info/btn lines logged on it are cropped there. An
    existing popup keeps its screen.png, like an existing menu."""
    name = e["popup"]
    d = templates_dir(game) / tree.COMMON / tree.POPUPS / name
    if name in folders and folders[name] != d:
        print(f"popup {name}: a menu has that name ({_rel(folders[name])}); skipped")
        log.warning(f"popup {name}: a menu has that name, skipping")
        return
    if d.is_dir():
        if name not in folders:
            print(f"popup {name}: exists ({_rel(d)}); screen.png kept, new capture is {e['screen']}")
    else:
        d.mkdir(parents=True)
        shutil.copy(ROOT / e["screen"], d / "screen.png")
        print(f"popup {name}: new popup {_rel(d)}")
        log.info(f"new popup {_rel(d)}")
    folders[name] = d


def _hash(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def _by_hand(path, started, cut):
    """True when image `path` changed after the session started and no finish
    of this session wrote it: a crop re-cut, edited or added by hand, which a
    re-cut from the log would replace. A session logged before `started` was
    recorded (None) has no such check. Content, not path, is what finish
    remembers, so `rename` (which keeps content) doesn't count as a change."""
    return started is not None and path.stat().st_mtime > started and _hash(path) not in cut


def _key(e):
    return e["kind"], e["here"], e["name"], tuple(e["box"]), bool(e.get("stay"))


def _score(match):
    return match[2] if match else 0.0


def score(targets, folder=None):
    """Score images on every capture in recon/map/ (or `folder`) and every
    saved screen*.png.

    targets: menu names or image paths; none means every menu the log touches.
    folder: score on the PNGs there instead of the session's captures; given
    image paths only, no mapping session is needed.
    For each image prints the captures it matches (THRESHOLD or more) with
    their scores, the best score among the rest, and the best score on a saved
    screen outside its own menu folder, flagging a match there.
    """
    if folder and targets and all((ROOT / t).is_file() for t in targets) and not LOG.exists():
        entries, game = [], Path(targets[0]).parts[0]
    else:
        entries = _entries()
        game = entries[0]["game"]
    menus, _ = tree.load(game)
    if not targets:
        targets = list(dict.fromkeys(n for e in entries if "kind" in e
                                     for n in (e["here"], e["name"]) if n in menus))
    images = []
    for t in targets:
        if t in menus:
            images += sorted((ROOT / menus[t]["path"]).glob("*_*.png"))
        elif (ROOT / t).is_file():
            images.append(ROOT / t)
        else:
            sys.exit(f"'{t}' is neither a menu of {game} nor an image")
    source = ROOT / folder if folder else DIR
    if not source.is_dir():
        sys.exit(f"No folder {folder}")
    captures = {p.stem: cv2.imread(str(p)) for p in sorted(source.glob("*.png"))}
    screens = {p: cv2.imread(str(p)) for p in sorted(templates_dir(game).rglob("screen*.png"))}
    for image in images:
        if not tree.ELEMENT.match(image.name):
            continue
        on = {n: _score(locate(image, s, threshold=0.0)) for n, s in captures.items()}
        hits = [f"{n} {s:.2f}" for n, s in on.items() if s >= THRESHOLD]
        rest = [(s, n) for n, s in on.items() if s < THRESHOLD]
        print(_rel(image))
        print("  matches: " + (", ".join(hits) or "none"))
        if rest:
            s, n = max(rest)
            print(f"  others at most {s:.2f} ({n})")
        away = [(_score(locate(image, s, threshold=0.0)), p) for p, s in screens.items()
                if p.parent != image.parent]
        if away:
            s, p = max(away)
            flag = "  <-- matches" if s >= THRESHOLD else ""
            print(f"  saved screens elsewhere at most {s:.2f} ({_rel(p)}){flag}")
    log.info(f"scored {len(images)} images on {len(captures)} captures and {len(screens)} screens")


SHEET = ROOT / "recon" / "sheet.png"  # outside recon/map/, whose PNGs are the captures
TILE_W = 480  # pixels per preview on the sheet


def sheet(names, box=None):
    """Save SHEET: the captures `names` (default: the session's last 8), 4 to a
    row, each labelled with its file name and a grid in device pixels."""
    if names:
        paths = [ROOT / n if (ROOT / n).is_file() else DIR / Path(n).name for n in names]
    else:
        paths = sorted(DIR.glob("*.png"))[-8:]
    missing = [p for p in paths if not p.is_file()]
    if missing or not paths:
        sys.exit(f"No capture {missing[0].name}" if missing else f"No captures in {_rel(DIR)}/")
    x0, y0, w, h = box or (0, 0, 1920, 1080)
    scale = TILE_W / w
    step = next((s for s in (20, 40, 80, 120, 240, 480) if s * scale >= 60), 480)
    tiles = [_tile(p, x0, y0, w, h, scale, step) for p in paths]
    while len(tiles) > 4 and len(tiles) % 4:
        tiles.append(tiles[0] * 0)
    rows = [cv2.hconcat(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(SHEET), cv2.vconcat(rows))
    log.debug(f"sheet of {len(paths)} captures, {_rel(SHEET)}")
    print(_rel(SHEET))


def _tile(path, x0, y0, w, h, scale, step):
    """One preview: the box of `path`, scaled, with a grid every `step` device pixels."""
    yellow, red, font = (0, 255, 255), (0, 0, 255), cv2.FONT_HERSHEY_SIMPLEX
    tile = cv2.resize(cv2.imread(str(path))[y0:y0 + h, x0:x0 + w], (TILE_W, round(h * scale)))
    for gx in range((x0 // step + 1) * step, x0 + w, step):
        px = round((gx - x0) * scale)
        cv2.line(tile, (px, 0), (px, tile.shape[0]), yellow, 1)
        cv2.putText(tile, str(gx), (px + 2, tile.shape[0] - 4), font, 0.35, yellow, 1)
    for gy in range((y0 // step + 1) * step, y0 + h, step):
        py = round((gy - y0) * scale)
        cv2.line(tile, (0, py), (TILE_W, py), yellow, 1)
        cv2.putText(tile, str(gy), (2, py - 2), font, 0.35, yellow, 1)
    cv2.putText(tile, path.name, (4, 18), font, 0.55, red, 2)
    return tile


def _scores_elsewhere(game, image, own):
    """(screen, score) for every saved screen outside menu folder `own`, best first."""
    scores = []
    for screen in sorted(templates_dir(game).rglob("screen*.png")):
        if screen.parent == own:
            continue
        scores.append((_rel(screen), _score(locate(image, screen, threshold=0.0))))
    return sorted(scores, key=lambda s: -s[1])


def unidentified(entries):
    """Menus the log touches that nothing will identify after finish: new menus
    with no info_ or button to another menu logged on them, and existing menus
    that have neither in the tree nor in the log (e.g. a menu whose only button
    leads to a menu that has no folder). goto can't recognise these."""
    menus, _ = tree.load(entries[0]["game"])
    new = [e["name"] for e in entries if e.get("kind") == "btn" and not e.get("stay")
           and e["name"] not in menus]
    marked = {e["here"] for e in entries
              if e.get("kind") == "info" or (e.get("kind") == "btn" and not e.get("stay"))}
    touched = [e["here"] for e in entries if e.get("kind") and e["here"] in menus]
    blind = [m for m in touched if not menus[m]["info"]
             and not any(b["name"] in menus for b in menus[m]["buttons"])]
    return [m for m in dict.fromkeys(new + blind) if m not in marked]


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _box(args):
    if len(args) != 4 or not all(a.isdigit() for a in args):
        sys.exit(__doc__)
    return list(map(int, args))


if __name__ == "__main__":
    setup(console=False)
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    fresh, stay, auto, moving = ("--fresh" in args, "--stay" in args, "--auto" in args,
                                 "--moving" in args)
    args = [a for a in args if a not in ("--fresh", "--stay", "--auto", "--moving")]
    opts = {}
    if "--box" in args:
        i = args.index("--box")
        opts["--box"] = _box(args[i + 1:i + 5])
        del args[i:i + 5]
    for flag in ("--on", "--after", "--in"):
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
        click(args[0], args[1], _box(args[2:]), fresh, stay, auto, moving)
    elif cmd == "back" and not args:
        back()
    elif cmd == "info" and len(args) == 6:
        info(args[0], args[1], _box(args[2:]), opts.get("--on"))
    elif cmd == "leads" and len(args) == 1:
        leads(args[0], opts.get("--after"))
    elif cmd == "popup" and len(args) == 1:
        popup(args[0], opts.get("--on"))
    elif cmd == "state" and len(args) == 2:
        state(args[0], args[1], opts.get("--on"))
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
    elif cmd == "score":
        score(args, opts.get("--in"))
    elif cmd == "sheet":
        sheet(args, opts.get("--box"))
    else:
        sys.exit(__doc__)
