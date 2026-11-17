# Daily types

The kinds of daily the three games share, so Claude can recognise one on a game it hasn't seen. Each type gives what to look for, which control does it, how a routine knows it's done, what it costs, and the routine to start from. The learn-dailies skill (`.claude/skills/learn-dailies/SKILL.md`) reads this file; it isn't imported by the games' `CLAUDE.md`, since only learning a game needs it.

A type is listed once two games show it, like everything in `core/notes/`. "Seen in one game" at the end lists the rest, so a new game is still checked for them; one moves up when a second game shows it. How each menu's screen is read (Lit or grey, Reading a zero, Lists that move…) is in `core/notes/UI.md`, cited as "(common: <section>)".

## Missions claim

The daily-missions menu (common: Daily missions). Look for **Missions, Tasks, Quests, Daily, Guide, Journal**, or a checklist or calendar icon with a red badge, on the lobby or one menu in.

- **Control:** one Claim All (re1999, ba) or the top chest on a points bar (e7), tapped while lit; a separate milestone Claim where Claim All leaves it (ba).
- **Done:** the control gone or grey.
- **Cost:** none.
- **Start from:** `re1999/routines/claim_dailies.py` (Claim All that disappears), `ba/routines/claim_dailies.py` (Claim All that greys, plus a milestone), `e7/routines/claim_dailies.py` (a points bar).
- **Also the checker.** Each row names a daily the game counts ("Claim mail 1/1", "Clear 3 stages 0/3"), so the menu is the list of what the game expects done, and a row's progress is how learn-dailies tells a routine worked. ba's rows have a blue Shortcut that opens the row's menu: a free route to discover.
- Runs last in the day's group, after the routines whose rows it claims (`e7/notes/routines.md`, `re1999/notes/routines.md`, `ba/notes/routines.md`).

## Idle claim

A resource that builds up over time and is collected: e7's Forest of Souls (Penguin Nest, Spirit Well, MolaGora Farm), re1999's Wilderness buildings, ba's Cafe Earnings. Look for a building, farm, cafe or base with a % badge, a full bar or a timer.

- **Control:** a Receive or Claim per source (e7's rows), one Claim on an earnings dialog (ba), or a pan-to-next icon and a tap on the resource (re1999).
- **Done:** the control grey, a timer in its place (e7), or the pan icon gone (re1999).
- **Cost:** none to collect. A second control next to the claim can spend a daily use (e7's Cultivate), so it's a step of its own.
- **Start from:** `e7/routines/claim_forest.py` (rows), `re1999/routines/claim_wilderness.py` (a 3D map, tapped as points), the earnings step of `ba/routines/cafe.py`.
- Often answered by a "Received" dialog per claim, or none (e7's MolaGora Farm), so the routine checks the control changed rather than waiting for a dialog.

## Limited attempts

Something the game hands out a few of each day (tickets, flags, chances, attempts) to spend on a fight or a stage: e7's arena flags and World Boss's 0/2; re1999's In-depth Analysis Chances; ba's bounty, scrimmage, lesson and Tactical Challenge tickets and Multi-Sweep's daily counts. Look for a small count by a mode's name ("Tickets 5/5", "Chances: 2", a flag with a number).

- **Control:** pick a target (the last stage cleared with full stars, the top opponent), then the mode's own way to finish a fight without playing it (below), until the count reads 0.
- **Done:** the count's first digit is 0 (common: Reading a zero), or the button grey.
- **Cost:** the attempts themselves, and often stamina too (ba's scrimmage 10 AP a ticket). Unused attempts are lost at reset, so spending them is usually wanted, but the user decides (learn-dailies' plan).
- **Start from:** `ba/routines/stage_sweep.py` (sweep MAX on a list), `ba/routines/tactical_challenge.py` (a PvP loop with skip), `e7/routines/run_arena.py` (a PvP loop with refresh and auto), `re1999/routines/pneuma_analysis.py` (replay with a multiplier).
- Which target is safe to pick is read from the screen (gold stars, a row not red), never fixed, since lists reorder as the account progresses (common: Lists that move).

## Stamina sink

Stages paid with stamina (e7: stamina; re1999: Activity; ba: AP), which refills over the day: e7's hunt, re1999's In Our Time and The Poussiere, ba's Hard sweeps. Look for a currency with a max (120/120) in the top bar and a cost on Start.

- **Control:** a fixed stage, then the fight-finishing way below. Each call spends a fixed amount.
- **Done:** one run, or a count of runs the routine was asked for. Running out shows as a refill offer, which costs premium currency, so the routine stops at it and never confirms it.
- **Cost:** stamina; a spend the user agrees to per routine and amount.
- **Start from:** `re1999/routines/poussiere.py` (replay at x4), `e7/routines/hunt.py` (background battling), `ba/routines/sweep_hard.py`.

## Finishing a fight without playing it

Every game has one, and it decides how simple the routine is. Look for these near Start, in this order:

| Way | Seen | What the routine does |
|---|---|---|
| Sweep / MAX / Multi-Sweep | ba (bounty, scrimmage, Hard) | set the count, confirm, close the summary; no fight screen |
| Replay of a recorded clear | re1999 (stage replay x1–x4) | switch to replay mode, start, wait for VICTORY |
| Background battling | e7 (hunt) | start it, come back later to claim (`e7/routines/check_background_status.py`) |
| Auto + skip | e7 (arena, World Boss: Auto), ba (Tactical Challenge: >>) | start, turn auto on or skip, wait for the result screen |

A fight that can only be played by hand isn't a daily the bot does.

## Social check-in

A daily the game counts for visiting or touching something, with nothing to win or lose: e7's guild check-in (entering the guild hall, done on the way to World Boss), re1999's lobby character (tapped for Bond), ba's cafe invite (a student's relationship). Look for missions rows like "Check in", "Interact", "Visit".

- **Control:** entering a menu, a tap on a character (a point, since characters change), or one invite.
- **Done:** often nothing on screen says so; the missions row is the only check.
- **Cost:** none, except an invite's cooldown (ba).
- **Start from:** `re1999/routines/lobby_interact.py`, the invite step of `ba/routines/cafe.py`.

## Seen in one game

- **Mail** (re1999's `claim_mail`): a Claim All that shows whether or not anything is left; a "nothing to claim" toast says done.
- **Free shop item** (e7's `claim_daily_shop`): a product priced Free in a daily shop tab, next to products that cost currency on the same grid.
- **Shop restock** (e7's `refresh_secret_shop`): buying given items from a list that changes; refreshing it costs premium currency.

## Never automatic

Whatever the type, these stay with the user and are never in a plan without their word for each: summons or recruits, anything paid in premium currency (gems, skystones, pyroxene) including stamina refills and shop refreshes, team building, and a fight with no way to finish it unplayed.
