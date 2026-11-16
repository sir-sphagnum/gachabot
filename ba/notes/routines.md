# Blue Archive routines

Named groups of routines the user asks for by one name. Each routine is in `ba/routines/` and registered in `ba.routines.ROUTINES`.

## daily tasks

`cafe lesson sweep_hard bounty scrimmage tactical_challenge`, after `start lobby`. Run them one at a time with `python -m core.device health` between them: BlueStacks' memory grows fast enough that the set needs a restart or two (`python -m core.device restart ba`) partway through (see notes/UI.md, start-screen).
