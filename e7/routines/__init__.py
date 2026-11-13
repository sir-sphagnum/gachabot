"""E7 routines (dailies, arena, ...), one module each.

A routine module exposes run() and is registered in ROUTINES so e7.bot can
run it by name, e.g.:

    # e7/routines/arena.py
    def run(): ...

    # here
    from e7.routines import arena
    ROUTINES = {"arena": arena.run}
"""

from e7.routines import claim_auto, claim_daily_shop, claim_forest, lobby, run_arena, start_screen

ROUTINES = {"start_screen": start_screen.run, "lobby": lobby.run,
            "claim_forest": claim_forest.run, "claim_auto": claim_auto.run,
            "claim_daily_shop": claim_daily_shop.run, "run_arena": run_arena.run}
