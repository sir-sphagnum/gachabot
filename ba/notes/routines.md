# Blue Archive routines

Named groups of routines the user asks for by one name. Each routine is in `ba/routines/` and registered in `ba.routines.ROUTINES`.

## daily tasks

`python -m ba.bot start lobby claim_mail sweep_hard cafe lesson bounty scrimmage tactical_challenge claim_dailies`. claim_dailies goes last, so the tasks the others complete are claimed. sweep_hard goes before cafe: it spends AP, and the cafe can't pay out its AP earnings while AP is at its cap (notes/UI.md, cafe, earnings-full). BlueStacks' memory grows fast enough that the set needs a restart or two partway through; `ba.bot` does them on its own (see notes/UI.md, start-screen).
