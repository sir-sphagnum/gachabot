# E7 routines

Named groups of routines the user asks for by one name. Each routine is in `e7/routines/` and registered in `e7.routines.ROUTINES`.

## daily routine

When the user says "run daily routine", run these in order:

1. guild check-in: `guild_check_in`
2. claim forest: `claim_forest`
3. claim daily shop: `claim_daily_shop`
4. wyvern hunt: `hunt` (its default hunt is wyvern)
5. arena: `run_arena`
6. claim dailies: `claim_dailies`

`claim_dailies` runs last because the others earn the daily missions' reputation (e.g. "[Daily] Nurture Spirit Bloom" is claim forest's Cultivate), and points earned after its claim wait for the next run.

All six in one command:

```bash
python -m e7.bot guild_check_in claim_forest claim_daily_shop hunt run_arena claim_dailies
```
