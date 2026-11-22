"""Unknown screens: captures nothing in a game's templates explains, saved
before the bot acts on them, for Claude to look at and map (unknown skill).

Usage: python -m core.unknown [GAME]               list the saved screens
       python -m core.unknown GAME done FILE ...   delete handled ones

Saved as logs/unknown/<game>/YYYYMMDD-HHMMSS-<routine>.png with a .json
beside it (.claude/logging.md §9). A screen already saved is not saved
again: its JSON counts the sighting instead.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import cv2

from core import ROOT, log as core_log, nav, steps, templates_dir
from core.log import LOGS, logger
from core.vision import difference, fingerprint, load, save as save_png

log = logger(__file__)

DIR = LOGS / "unknown"
# Percent of pixels (core.vision.difference) under which a capture is a
# screen already saved: the scale tools.dedupe uses for recon frames.
SAME = 1.0
CLOSEST = 5  # identifiers listed with their best score, best first

_warned = set()  # saves this process has logged at WARNING; repeats go to DEBUG


def save(game, screen, doing):
    """Save `screen`, a capture nothing of `game`'s explains, and log where.

    doing: what the caller does next ("pressing back 3/10", "giving up"),
        written in the JSON and the log line.
    Returns the PNG's path, or None (logged as a WARNING) when it couldn't be
    written: a failed save never stops the caller.
    """
    try:
        return _save(game, load(screen), doing)
    except Exception as e:
        log.warning(f"unknown screen not saved: {e}")
        return None


def _save(game, screen, doing):
    folder = DIR / game
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    mark = _print(screen)
    for png in sorted(folder.glob("*.png")):
        if difference(mark, _print(load(png))) < SAME:
            meta = _read(png)
            meta.update(count=meta.get("count", 1) + 1, last=now, last_doing=doing)
            _write(png, meta)
            _say(png, f"unknown screen again ({meta['count']} times): {_rel(png)}, {doing}")
            return png
    routine, _ = steps.caller()
    # A caller can be "<string>" (python -c) or "<stdin>": not a file name on Windows.
    stem = f"{datetime.now():%Y%m%d-%H%M%S}-{re.sub(r'[^A-Za-z0-9_.-]', '', routine) or 'core'}"
    png = folder / f"{stem}.png"
    n = 2
    while png.exists():
        png = folder / f"{stem}-{n}.png"
        n += 1
    save_png(screen, png)
    _write(png, {"game": game, "run": _run(), "routine": routine, "first": now, "last": now,
                 "count": 1, "doing": doing, "uptime": _uptime(game),
                 "closest": closest(game, screen)})
    _say(png, f"unknown screen: {_rel(png)}, {doing}")
    return png


def closest(game, screen, n=CLOSEST):
    """The `n` info_ images of `game` (menus, popups, stops, loads) that come
    closest on `screen`, as [{"template", "score"}], best first. A known
    identifier just under the match threshold points at a screen that moved
    or a layout gone wrong, not at a new screen."""
    base = templates_dir(game)
    scores = []
    for t in base.rglob("info_*.png"):
        hit = nav.locate(t, screen, threshold=0.0)
        if hit:
            scores.append({"template": t.relative_to(base).as_posix(), "score": round(hit[2], 2)})
    return sorted(scores, key=lambda s: -s["score"])[:n]


def entries(game=None):
    """[(png, meta)] of the saved screens, of `game` or of every game, oldest first."""
    folders = [DIR / game] if game else sorted(p for p in DIR.glob("*") if p.is_dir())
    return [(png, _read(png)) for f in folders for png in sorted(f.glob("*.png"))]


def done(game, names):
    """Delete the named saves (file names or paths) of `game`. Returns the names not found."""
    missing = []
    for name in names:
        png = DIR / game / Path(name).with_suffix(".png").name
        if not png.exists():
            missing.append(name)
            continue
        png.unlink()
        png.with_suffix(".json").unlink(missing_ok=True)
    return missing


def _say(png, line):
    if png in _warned:
        log.debug(line)
    else:
        _warned.add(png)
        log.warning(line)


def _print(screen):
    return fingerprint(cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY))


def _read(png):
    meta = png.with_suffix(".json")
    return json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}


def _write(png, meta):
    png.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def _run():
    return core_log.RUN  # read at save time: setup(run=...) sets it after import


def _uptime(game):
    try:
        from core.device import uptime
        return uptime(game)
    except Exception:  # adb gone: the save matters more than this field
        return None


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("game", nargs="?", help="the game's folder name (e.g. e7); all games when left out")
    p.add_argument("cmd", nargs="?", choices=["done"], help="done: delete the FILEs, once handled")
    p.add_argument("files", nargs="*")
    a = p.parse_args()
    if a.cmd == "done":
        if not a.game or not a.files:
            sys.exit("Usage: python -m core.unknown GAME done FILE ...")
        missing = done(a.game, a.files)
        for name in missing:
            print(f"Not found: {name}")
        print(f"Deleted {len(a.files) - len(missing)}")
        return 1 if missing else 0
    found = entries(a.game)
    if not found:
        print("No unknown screens saved")
        return 0
    for png, meta in found:
        near = ", ".join(f"{c['template']} {c['score']:.2f}" for c in meta.get("closest", []))
        print(f"{_rel(png)}  x{meta.get('count', 1)}  {meta.get('first')} .. {meta.get('last')}"
              f"  {meta.get('routine')} ({meta.get('run')}): {meta.get('doing')}"
              + (f"\n    closest: {near}" if near else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
