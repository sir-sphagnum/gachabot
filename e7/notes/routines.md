# E7 routines

Named groups of routines the user asks for by one name. Each routine is in `e7/routines/` and registered in `e7.routines.ROUTINES`.

## daily routine

When the user says "run daily routine", run these in order:

1. claim forest: `claim_forest`
2. claim daily shop: `claim_daily_shop`
3. secret shop: `refresh_secret_shop` (buys what the current list has; no skystone refreshes)
4. world boss: `world_boss` (also the day's guild check-in: it goes through the guild hall)
5. wyvern hunt: `hunt` (its default hunt is wyvern)
6. arena: `run_arena`
7. claim dailies: `claim_dailies`

`claim_dailies` runs last because the others earn the daily missions' reputation (e.g. "[Daily] Nurture Spirit Bloom" is claim forest's Cultivate), and points earned after its claim wait for the next run.

All seven in one command:

```bash
python -m e7.bot claim_forest claim_daily_shop refresh_secret_shop world_boss hunt run_arena claim_dailies
```
