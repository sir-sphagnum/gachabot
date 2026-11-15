# E7 routines

Named groups of routines the user asks for by one name. Each routine is in `e7/routines/` and registered in `e7.routines.ROUTINES`.

## daily routine

When the user says "run daily routine", run these in order:

1. claim forest: `claim_forest`
2. claim daily shop: `claim_daily_shop`
3. wyvern hunt: `hunt` (its default hunt is wyvern)
4. arena: `run_arena`

All four in one command:

```bash
python -m e7.bot claim_forest claim_daily_shop hunt run_arena
```
