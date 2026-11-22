"""Project Neural Cloud routines, one module each.

A routine module exposes run() and is registered in ROUTINES so nc.bot can
run it by name, e.g.:

    # nc/routines/arena.py
    def run(): ...

    # here
    from nc.routines import arena
    ROUTINES = {"arena": arena.run}

core.device restart runs the "lobby" entry after starting the game, and
core.nav loads nc/routines/lobby.py by name, so keep both names.
"""

from nc.routines import lobby

ROUTINES = {"lobby": lobby.run}
