"""Rank the bot's steps by how often they need help, from logs/steps.jsonl.

Usage: python -m tools.steps [--game GAME] [--routine ROUTINE] [--days N]

One row per (routine, kind, button), flagged rows first:
  calls   calls recorded       runs   distinct runs they came from
  taps    mean taps per call (tap_until, close_popup)
  retry%  calls that needed more than one tap (held: whose result flickered)
  skip%   calls with a tap skipped because the button wasn't on screen
  popup%  calls that closed a popup on the way (tap_until)
  fail%   calls that returned no result
  max s   slowest call
A row is flagged (!) when retry% or skip% is above FLAG. A flag says where
to look, not what's wrong: read the step's error screen or run log next.
Fields of the file: .claude/logging.md §8.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from core.steps import FILE

FLAG = 20  # percent


def load(path=FILE, game=None, routine=None, days=None):
    since = datetime.now() - timedelta(days=days) if days else None
    lines = []
    if not path.exists():
        return lines
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            line = json.loads(raw)
        except ValueError:
            continue  # a line cut short by a killed process
        if game and line.get("game") != game:
            continue
        if routine and line.get("routine") != routine:
            continue
        if since and datetime.fromisoformat(line["t"]) < since:
            continue
        lines.append(line)
    return lines


def table(lines):
    groups = defaultdict(list)
    for line in lines:
        groups[line["routine"], line["kind"], line["button"]].append(line)
    rows = []
    for (routine, kind, button), calls in groups.items():
        n = len(calls)

        def pct(test):
            return 100 * sum(1 for c in calls if test(c)) / n

        tapped = kind != "held"
        rows.append({
            "step": f"{routine}: {button}" + ("" if kind == "tap_until" else f" ({kind})"),
            "calls": n,
            "runs": len({c.get("run") for c in calls}),
            "taps": sum(c.get("taps", 0) for c in calls) / n if tapped else None,
            "retry": pct(lambda c: c.get("taps", 0) > 1 if tapped else c.get("flickers", 0) > 0),
            "skip": pct(lambda c: c.get("skipped", 0) > 0) if tapped else None,
            "popup": pct(lambda c: c.get("popups", 0) > 0) if kind == "tap_until" else None,
            "fail": pct(lambda c: not c.get("ok")),
            "max": max(c.get("s", 0) for c in calls),
        })
    for r in rows:
        r["flag"] = r["retry"] > FLAG or (r["skip"] or 0) > FLAG
    rows.sort(key=lambda r: (not r["flag"], -r["retry"], -(r["skip"] or 0), -r["calls"]))
    return rows


def _cell(value, fmt):
    return "-" if value is None else format(value, fmt)


def show(rows):
    if not rows:
        print(f"No steps recorded in {FILE.name} for these filters")
        return
    width = max(len(r["step"]) for r in rows)
    print(f"  {'step':<{width}}  calls  runs  taps  retry%  skip%  popup%  fail%  max s")
    for r in rows:
        print(f"{'!' if r['flag'] else ' '} {r['step']:<{width}}  {r['calls']:>5}  {r['runs']:>4}"
              f"  {_cell(r['taps'], '4.1f'):>4}  {r['retry']:>6.0f}  {_cell(r['skip'], '5.0f'):>5}"
              f"  {_cell(r['popup'], '6.0f'):>6}  {r['fail']:>5.0f}  {r['max']:>5.1f}")
    flagged = sum(r["flag"] for r in rows)
    if flagged:
        print(f"\n{flagged} step(s) flagged: retry% or skip% above {FLAG}")


def _main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--game", help="only this game's steps (e.g. e7)")
    p.add_argument("--routine", help="only this routine's steps (e.g. run_arena)")
    p.add_argument("--days", type=float, help="only the last N days")
    a = p.parse_args()
    show(table(load(game=a.game, routine=a.routine, days=a.days)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
