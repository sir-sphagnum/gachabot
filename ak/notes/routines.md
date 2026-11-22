# Arknights routines

Named groups of routines the user asks for by one name. Each routine is in `ak/routines/` and registered in `ak.routines.ROUTINES`.

## daily routine

`python -m ak.bot start lobby claim_mail base_collect claim_credit run_stage claim_dailies`. The claims cost nothing; run_stage spends 126 Sanity (14 runs of 1-12, ~25 minutes). `claim_dailies` runs last because the others count towards the Daily missions.
