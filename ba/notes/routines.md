# Blue Archive routines

Named groups of routines the user asks for by one name. Each routine is in `ba/routines/` and registered in `ba.routines.ROUTINES`.

## daily tasks

`python -m ba.bot start lobby claim_mail cafe lesson sweep_hard bounty scrimmage tactical_challenge claim_dailies`. claim_dailies goes last, so the tasks the others complete are claimed. BlueStacks' memory grows fast enough that the set needs a restart or two partway through; `ba.bot` does them on its own (see notes/UI.md, start-screen).
