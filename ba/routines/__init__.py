"""Blue Archive routines, one module each.

A routine module exposes run() and is registered in ROUTINES so ba.bot can
run it by name, e.g.:

    # ba/routines/arena.py
    def run(): ...

    # here
    from ba.routines import arena
    ROUTINES = {"arena": arena.run}

core.device restart runs the "start_screen" and "lobby" entries after
starting the game, and core.nav loads ba/routines/lobby.py by name, so
keep both names.
"""

from ba.routines import lobby, start_screen

ROUTINES = {"start_screen": start_screen.run, "lobby": lobby.run}
