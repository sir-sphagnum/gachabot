"""Check a game's mapped tree on the live game, or record a cold start, and
report every screen the templates can't explain.

Usage: python -m tools.probe GAME walk [--from MENU] [--max N]
       python -m tools.probe GAME cold

walk  for each menu under MENU (default: the lobby), in route order:
      goto it, read the screen with core.nav.where, press the game's BACK_KEY
      and read where that lands. It taps only the buttons goto takes, all
      of them edges between mapped menus, and skips every menu whose route
      has a button or menu named with a word that can spend
      (core.tree.SPEND_WORDS), so nothing is bought, fought or used up. It
      never presses Back on the lobby (that opens the quit dialog). Stops
      after N menus (default 40): every capture adds to BlueStacks' memory.
cold  force-stop the game, then launch it and run its start_screen and lobby
      routines while a second thread saves the screen each second it changes.
      Frames that are black, a loading screen (templates/common/loading/), a
      known popup or a menu are explained; the rest go in the report, one
      line per stretch of consecutive frames: an unmapped splash or load, or
      a popup or dialog, usually a first-of-the-day one (core/notes/UI.md,
      First of the day or week). Run it on the first launch after the game's
      daily reset.

Both write recon/probe/report.md (replaced each run) with the captures it
cites in recon/probe/, and print its path. walk also keeps each menu's best
identifier score in recon/probe/scores.json and flags a score that fell
by more than DROP since the last walk: something on the menu moved.
Before either, it checks core.device health and stops when it fails.
"""

import argparse
import importlib
import json
import shutil
import sys
import threading
import time
from datetime import datetime

import cv2

from core import ROOT, device, tree
from core.input import back, capture
from core.log import logger, setup
from core.nav import HOME, check_focus, goto, loading, route, where
from core.vision import difference, fingerprint, is_black, save

log = logger(__file__)

DIR = ROOT / "recon" / "probe"
REPORT = DIR / "report.md"
SCORES = DIR / "scores.json"
DROP = 0.05       # a best identifier score this much under the last walk's is flagged
LEAVE_WAIT = 3    # seconds after Back for the menu to go
BACK_WAIT = 10    # seconds after that for a known screen (a load can come first)
CHANGED = 1.0     # percent of pixels (core.vision.difference) for cold to save a frame
INTERVAL = 1.0    # seconds between cold's captures


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def _save(img, label):
    n = len(list(DIR.glob("*.png")))
    path = DIR / f"{n:03d}-{label}.png"
    save(img, path)
    return _rel(path)


def _fresh_dir():
    shutil.rmtree(DIR / "cold", ignore_errors=True)
    for f in DIR.glob("*.png"):
        f.unlink()
    DIR.mkdir(parents=True, exist_ok=True)


def _healthy():
    ok, msg = device.health()
    if not ok:
        print(f"Health check failed: {msg}")
    return ok


def _describe(game, screen):
    """(popups, menus) on `screen` as one line for the report."""
    popups, menus = where(game, screen)
    parts = [f"popup_{p}" for p in popups]
    parts += [f"{m} ({t} {s:.2f})" for m, t, s in menus]
    return popups, menus, ", ".join(parts) or "nothing known"


def _print(screen):
    return fingerprint(cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY))


def _known(game, screen):
    """`screen` when a popup or menu of `game` shows on it, else None."""
    popups, menus = where(game, screen)
    return screen if popups or menus else None


def _blocked(steps):
    """The first menu on a route named with a spend word, or None. A route's
    buttons are named after the menus they open, so this covers both."""
    return next((b["name"] for _, b in steps if tree.spends(b["name"])), None)


def walk(game, start=HOME, limit=40):
    menus, problems = tree.load(game)
    if start not in menus:
        sys.exit(f"No menu '{start}' in {game}")
    check_focus(game)
    key = importlib.import_module(f"{game}.config").BACK_KEY
    old = json.loads(SCORES.read_text(encoding="utf-8")) if SCORES.exists() else {}
    new = dict(old)
    lines = []

    order = []
    for name in menus:
        steps = route(menus, HOME, name)
        if steps is None:
            continue
        path = [HOME, *(b["name"] for _, b in steps)]
        if start in path:
            order.append((len(path), name, steps))
    order.sort(key=lambda o: (o[0], o[1]))

    findings, seen = [], 0
    for _, name, steps in order:
        if seen == limit:
            findings.append(f"- stopped after {limit} menus (--max)")
            break
        blocked = _blocked(steps)
        if blocked:
            findings.append(f"- {name}: not probed, its route has `{blocked}`, which may spend")
            continue
        seen += 1
        log.info(f"probing {name}")
        if not goto(game, name):
            screen = capture()
            shot = _save(screen, f"unreached-{name}")
            _, _, said = _describe(game, screen)
            findings.append(f"- **{name}: not reached.** Screen shows {said}. `{shot}`")
            continue
        screen = capture()
        popups, found, said = _describe(game, screen)
        others = [m for m, _, s in found if m != name]
        own = next((s for m, _, s in found if m == name), None)
        if own is not None:
            new[name] = round(own, 2)
            if name in old and own < old[name] - DROP:
                findings.append(f"- {name}: identifier score fell, {old[name]:.2f} -> {own:.2f}. "
                                f"`{_save(screen, f'drop-{name}')}`")
        if others:
            findings.append(f"- **{name}: collision**, also matches {said}. "
                            f"`{_save(screen, f'collision-{name}')}`")
        if popups:
            findings.append(f"- {name}: popup open on entry ({said}). `{_save(screen, f'popup-{name}')}`")
        if name == HOME:
            lines.append(f"- {name}: {said}")
            continue
        back(key)
        # First the menu must go (Back answers late; a changed screen proves
        # nothing on an animated one), unless Back does nothing here. Then a
        # load can show (re1999 leaves wilderness through ~5 s of an unmapped
        # loading screen), so a screen counts as unknown only once BACK_WAIT
        # has passed without a known one.
        device.wait_until(lambda: name not in (m for m, _, _ in where(game, capture())[1]),
                          LEAVE_WAIT)
        after = device.wait_until(lambda: _known(game, capture()), BACK_WAIT)
        after = capture() if after is None else after
        popped, landed, said_after = _describe(game, after)
        lines.append(f"- {name}: {said}; Back -> {said_after}")
        if not (popped or landed or is_black(after)):
            findings.append(f"- **{name}: Back led to an unknown screen.** `{_save(after, f'back-{name}')}`")

    SCORES.write_text(json.dumps(new, indent=1, sort_keys=True), encoding="utf-8")
    report = [f"# Probe walk: {game} from {start}", "", f"{datetime.now():%Y-%m-%d %H:%M}", "",
              "## Findings", "", *(findings or ["- none"]), ""]
    if problems:
        report += ["## Tree problems (core.tree)", "", *(f"- {p}" for p in problems), ""]
    report += ["## Menus (what each read, and where Back went)", "", *lines]
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    log.info(f"walk done, {seen} menus, {len(findings)} findings")
    return findings


def _record(folder, stop):
    """Save the screen to `folder` each INTERVAL while it changes, until `stop` is set."""
    folder.mkdir(parents=True, exist_ok=True)
    last = None
    while not stop.is_set():
        t = time.monotonic()
        try:
            img = capture()
        except RuntimeError as e:  # empty frames, AdbTimeout
            log.warning(f"capture failed ({e}), going on")
        else:
            now = _print(img)
            if last is None or difference(last, now) > CHANGED:
                save(img, folder / f"{datetime.now():%H%M%S}.png")
                last = now
        stop.wait(max(0.0, INTERVAL - (time.monotonic() - t)))


def cold(game):
    frames = DIR / "cold"
    stop = threading.Event()
    log.info(f"cold start of {game}")
    device.stop_game(game)
    recorder = threading.Thread(target=_record, args=(frames, stop), daemon=True)
    recorder.start()
    started = time.monotonic()
    try:
        ok = device.start_game(game) and device.run_to_lobby(game)
    finally:
        stop.set()
        recorder.join()
    took = time.monotonic() - started
    lines = [f"# Probe cold start: {game}", "", f"{datetime.now():%Y-%m-%d %H:%M}", "",
             f"Launch to lobby: {'reached' if ok else '**not reached**'} in {took:.0f}s.", "",
             "## Screens nothing identifies (first and last capture of each stretch)", ""]
    # Consecutive unknown captures are one stretch: usually one screen (a
    # splash, an unmapped load, a popup) captured each second it changed.
    stretches, timeline, run = [], [], []
    for f in sorted(frames.glob("*.png")):
        screen = cv2.imread(str(f))
        if is_black(screen):
            continue
        said = "loading" if loading(game, screen) else _describe(game, screen)[2]
        timeline.append(f"- {f.stem}: {said}")
        if said == "nothing known":
            run.append(f)
        elif run:
            stretches.append(run)
            run = []
    if run:
        stretches.append(run)
    unknown = [f"- {r[0].stem}" + (f" to {r[-1].stem}" if len(r) > 1 else "")
               + f" ({len(r)} captures): `{_rel(r[0])}`" + (f", `{_rel(r[-1])}`" if len(r) > 1 else "")
               for r in stretches]
    lines += (unknown or ["- none"]) + ["", "## Timeline", ""] + timeline
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"cold start done, lobby {'reached' if ok else 'not reached'}, "
             f"{len(stretches)} unknown stretches")
    return ok, unknown


def _main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("game")
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("walk", help="goto each mapped menu, read it, press Back")
    w.add_argument("--from", dest="start", default=HOME, help="the subtree's top menu")
    w.add_argument("--max", type=int, default=40, help="menus to probe at most")
    sub.add_parser("cold", help="record a cold start and report unknown screens")
    a = p.parse_args()
    setup(run=f"{__spec__.name}-{a.game}-{a.cmd}")
    if a.game not in tree.games():
        sys.exit(f"No game '{a.game}'. Games: {', '.join(tree.games())}")
    if not _healthy():
        return 1
    _fresh_dir()
    if a.cmd == "walk":
        walk(a.game, a.start, a.max)
    else:
        cold(a.game)
    print(_rel(REPORT))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
