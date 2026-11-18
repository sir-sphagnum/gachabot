"""E7 routines (dailies, arena, ...), one module each.

A routine module exposes run() and is registered in ROUTINES so e7.bot can
run it by name, e.g.:

    # e7/routines/arena.py
    def run(): ...

    # here
    from e7.routines import arena
    ROUTINES = {"arena": arena.run}
"""

from e7.routines import (check_background_status, claim_dailies, claim_daily_shop, claim_forest, claim_mail, hunt,
                         lobby, refresh_secret_shop, run_arena, start_screen, world_boss)

ROUTINES = {"start_screen": start_screen.run, "lobby": lobby.run,
            "claim_forest": claim_forest.run, "check_background_status": check_background_status.run,
            "claim_daily_shop": claim_daily_shop.run, "run_arena": run_arena.run,
            "claim_dailies": claim_dailies.run, "claim_mail": claim_mail.run, "hunt": hunt.run,
            "refresh_secret_shop": refresh_secret_shop.run,
            "world_boss": world_boss.run}
