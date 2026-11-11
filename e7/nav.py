"""Go to any E7 menu mapped under e7/templates/, from wherever the game is.

Usage: python -m e7.nav TARGET [--here MENU]
       python -m e7.nav --list

TARGET  a menu folder name (e.g. forest-of-souls).
--here  the menu already on screen: walk from it instead of from the lobby.
--list  print each menu's route from the lobby, without touching the game.

Walks start from the active lobby (the lobby routine gets there from
anywhere, closing popups on the way), then tap down the tree with
core.nav.goto. Only menus some chain of btn_ images reaches from the lobby
can be reached; the start screen can't.
"""

import argparse
import sys

from core import tree
from core.nav import goto, route
from e7.config import GAME
from e7.routines import lobby

HOME = "lobby"


def run(target, here=None, verbose=True):
    """Return True once `target` is on screen, False if it couldn't get there."""
    menus, _ = tree.load(GAME)
    wake = lambda: lobby.run(verbose=verbose)
    # The lobby hides its HUD after ~9 s idle, so wake it before each tap on it.
    return goto(menus, target, home=wake, start=HOME, here=here,
                ready={HOME: wake}, verbose=verbose)


def routes():
    """{menu: [menu names from HOME to it], or None when unreachable}."""
    menus, _ = tree.load(GAME)
    out = {}
    for name in menus:
        steps = route(menus, HOME, name)
        out[name] = None if steps is None else [HOME, *(b["name"] for _, b in steps)]
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("target", nargs="?")
    p.add_argument("--here")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()
    if a.list:
        for name, path in routes().items():
            print(f"{name}: {' > '.join(path) if path else '(not reachable from the lobby)'}")
        sys.exit(0)
    if not a.target:
        sys.exit(__doc__)
    menus, _ = tree.load(GAME)
    if a.target not in menus:
        sys.exit(f"No menu '{a.target}'. Menus: {', '.join(menus)}")
    if a.here and a.here not in menus:
        sys.exit(f"No menu '{a.here}'. Menus: {', '.join(menus)}")
    sys.exit(0 if run(a.target, a.here) else 1)
