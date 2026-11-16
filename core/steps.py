"""Step statistics: one JSON line per tap_until, close_popup and held call,
appended to logs/steps.jsonl. Rules and fields: .claude/logging.md §8.
Read with `python -m tools.steps`.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from core import ROOT, log

FILE = log.LOGS / "steps.jsonl"
CORE = ROOT / "core"

_log = log.logger(__file__)


def caller():
    """(routine, line) of the first frame outside core/: the routine module
    that made the call, named by file stem like its logger, and the line it
    called from. ("core", 0) when core itself is the caller (core.nav's
    command line)."""
    frame = sys._getframe(1)
    while frame:
        path = Path(frame.f_code.co_filename).resolve()
        if CORE not in path.parents:
            return path.stem, frame.f_lineno
        frame = frame.f_back
    return "core", 0


def name(target):
    """How a step's button or check appears in the lines: a template's file
    name, a point as "x,y@routine:line", a check by its function name
    (a lambda as "check@routine:line")."""
    if isinstance(target, (str, Path)):
        return Path(target).name
    routine, line = caller()
    if isinstance(target, tuple):
        return f"{target[0]},{target[1]}@{routine}:{line}"
    fn = getattr(target, "__name__", "check")
    return fn if fn != "<lambda>" else f"check@{routine}:{line}"


def game(*targets):
    """The game whose templates (<game>/templates/...) are among `targets`, or
    the game folder the calling routine lives in, or None."""
    for t in targets:
        if isinstance(t, (str, Path)):
            parts = _parts(t)
            if len(parts) > 1 and parts[1] == "templates":
                return parts[0]
    frame = sys._getframe(1)
    while frame:
        parts = _parts(frame.f_code.co_filename)
        if len(parts) > 2 and parts[1] == "routines":
            return parts[0]
        frame = frame.f_back
    return None


def _parts(path):
    try:
        return Path(path).resolve().relative_to(ROOT).parts
    except ValueError:
        return ()


def record(kind, button, **fields):
    """Append one line for a finished step. Never raises: statistics must not
    break the run they describe."""
    try:
        routine, _ = caller()
        line = {"t": datetime.now().isoformat(timespec="seconds"), "run": log.RUN,
                "game": fields.pop("game", None), "routine": routine, "kind": kind,
                "button": button, **fields}
        FILE.parent.mkdir(exist_ok=True)
        with FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
    except Exception as e:
        _log.warning(f"step not recorded: {e}")
