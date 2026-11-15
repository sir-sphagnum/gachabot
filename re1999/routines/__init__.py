"""Reverse: 1999 routines, one module each.

A routine module exposes run() and is registered in ROUTINES so re1999.bot can
run it by name, e.g.:

    # re1999/routines/arena.py
    def run(): ...

    # here
    from re1999.routines import arena
    ROUTINES = {"arena": arena.run}

core.device restart runs the "start_screen" entry after starting the game,
and core.nav loads re1999/routines/lobby.py by name, so keep both names.
"""

from re1999.routines import lobby, start_screen

ROUTINES = {"start_screen": start_screen.run, "lobby": lobby.run}
