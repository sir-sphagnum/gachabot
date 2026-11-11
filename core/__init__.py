"""Game-agnostic BlueStacks automation. Never imports a game package (e.g. e7).

Layers, each importing only the ones above it:
    adb     connect to BlueStacks, run adb commands
    input   tap, back, capture/screenshot
    vision  template matching and cropping (no device access)
    device  focus, fullscreen, start/stop apps, wait_until
    tree    read the menu trees under <game>/templates/
    nav     tap_until, popup handling, walking the menu tree
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def templates_dir(game):
    """A game's template folder: <game>/templates/ next to core/ (e.g. e7/templates/)."""
    return ROOT / game / "templates"
