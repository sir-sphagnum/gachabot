"""Game-agnostic automation of the Android emulator. Never imports a game package directly
(e.g. `from e7 import ...`): the only game code it runs is a game's lobby
routine, which nav loads by name from the game it is given.

Layers, each importing only the ones above it:
    log     log line format, per-module loggers, skill log files, error
            screenshots (.claude/logging.md); imports input only when saving one
    adb     connect to the emulator, run adb commands
    input   tap, back, capture/screenshot
    vision  template matching and cropping (no device access)
    device  focus, start/stop apps, emulator health and restarts, wait_until
    tree    read the menu trees under <game>/templates/
    steps   step statistics: one line per tap_until/close_popup/held call
            in logs/steps.jsonl (.claude/logging.md §8)
    nav     tap_until, popup handling, walking the menu tree from the
            game's lobby (<game>/routines/lobby.py)
    unknown save screens nothing in a game's templates explains
            (logs/unknown/, .claude/logging.md §9)
    lobby   the loop from launch through the start screen to the lobby,
            run from each game's spec (<game>/routines/lobby.py)
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def templates_dir(game):
    """A game's template folder: <game>/templates/ next to core/ (e.g. e7/templates/)."""
    return ROOT / game / "templates"
