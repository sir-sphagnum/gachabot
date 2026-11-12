"""Logging for routines, navigation and the commands skills run. Rules: .claude/logging.md.

Usage: python -m core.log start SKILL
       python -m core.log end [--all]

Modules take their logger with `log = logger(__file__)`; command-line entry
points call setup() once.

Skill logs: a skill run (recon, map, navigate...) keeps one file,
logs/YYYYMMDD-HHMMSS-SKILL.log. `start` opens it and `end` closes it. In
between, every process that calls setup() also writes its lines there, at
every level, so the file holds the whole run even though it spans many
commands (a background recon loop, one process per tap). A skill started
while one is open is nested: it logs into the open file, and its `end`
leaves that file open for the outer skill. `end --all` closes the file
whatever is nested, for one left open by a run that never ended.
"""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from core import ROOT

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATEFMT = "%H:%M:%S"

LOGS = ROOT / "logs"
# The open skill log: its file name on the first line, then one line per
# skill started and not yet ended, outermost first.
CURRENT = LOGS / "current"

log = logging.getLogger("log")


def logger(file):
    """The logger for the module in `file`, named after it (e.g. "lobby").

    Named from the file, not __name__: under `python -m e7.routines.lobby`,
    __name__ is "__main__"."""
    return logging.getLogger(Path(file).stem)


def setup(debug=False, console=True):
    """Send log lines in FORMAT to the open skill log, if any, at every level,
    and to the terminal: INFO and above, or everything with debug.

    console=False: not to the terminal. For commands whose output is a printed
    answer (.claude/logging.md §1), so what they did reaches the skill log
    without doubling their answer on screen.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    fmt = logging.Formatter(FORMAT, DATEFMT)
    if console:
        term = logging.StreamHandler()
        term.setLevel(logging.DEBUG if debug else logging.INFO)
        term.setFormatter(fmt)
        root.addHandler(term)
    path = _open()[0]
    if path:
        file = logging.FileHandler(path, encoding="utf-8")
        file.setFormatter(fmt)
        root.addHandler(file)
    if not root.handlers:
        root.addHandler(logging.NullHandler())  # else WARNINGs fall back to stderr


def _open():
    """(path of the open skill log, [skills started, outermost first]), or
    (None, []) when none is open."""
    if not CURRENT.exists():
        return None, []
    name, *skills = CURRENT.read_text(encoding="utf-8").split()
    return LOGS / name, skills


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def start(skill):
    path, skills = _open()
    if not path:
        LOGS.mkdir(exist_ok=True)
        path = LOGS / f"{datetime.now():%Y%m%d-%H%M%S}-{skill}.log"
    CURRENT.write_text("\n".join([path.name, *skills, skill]) + "\n", encoding="utf-8")
    setup(console=False)
    log.info(f"{skill} started" + (f", inside {skills[-1]}" if skills else ""))
    print(f"Logging to {_rel(path)}" + (f" (inside {', '.join(skills)})" if skills else ""))


def end(everything=False):
    path, skills = _open()
    if not path:
        print("No skill log open")
        return
    setup(console=False)
    ended = skills if everything else skills[-1:]
    for skill in reversed(ended):
        log.info(f"{skill} ended")
    rest = skills[:len(skills) - len(ended)]
    if rest:
        CURRENT.write_text("\n".join([path.name, *rest]) + "\n", encoding="utf-8")
        print(f"Ended {', '.join(ended)}; {_rel(path)} stays open for {rest[-1]}")
        return
    CURRENT.unlink()
    logging.shutdown()  # flush before counting
    lines = len(path.read_text(encoding="utf-8").splitlines())
    print(f"Closed {_rel(path)} ({lines} lines)")


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    if cmd == "start" and len(args) == 1 and re.fullmatch(r"[a-z0-9-]+", args[0]):
        start(args[0])
    elif cmd == "end" and args in ([], ["--all"]):
        end(everything=bool(args))
    else:
        sys.exit(__doc__)
