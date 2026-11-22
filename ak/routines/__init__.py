"""Arknights routines, one module each.

A routine module exposes run() and is registered in ROUTINES so ak.bot can
run it by name, e.g.:

    # ak/routines/arena.py
    def run(): ...

    # here
    from ak.routines import arena
    ROUTINES = {"arena": arena.run}

core.device restart runs the "lobby" entry after starting the game, and
core.nav loads ak/routines/lobby.py by name, so keep both names.
"""

from ak.routines import (base_collect, claim_credit, claim_dailies, claim_mail, lobby,
                         run_stage)

ROUTINES = {
    "lobby": lobby.run,
    "claim_mail": claim_mail.run,
    "base_collect": base_collect.run,
    "claim_credit": claim_credit.run,
    "run_stage": run_stage.run,
    "claim_dailies": claim_dailies.run,
}
