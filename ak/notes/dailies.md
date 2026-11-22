# Arknights dailies

The daily missions as the game lists them, the routine that does each, and what it costs. learn-dailies made it; `ak/notes/routines.md` has the command that runs them in order.

Missions' Daily tab lists rows that each pay stamps when claimed (the ×1 / ×2 by each row's tower), and the reward sets 000–009 on the left take them in order: 000 one stamp, 001–006 two, 007–009 three, 22 in all. The goal is every set claimed (common: Daily missions). A claimed row often comes back as its next tier (Trust 5 → 10, clear 1 → 4 stages, defeat 100 → 200 enemies, 1 → 3 leaders), so the list grows as the day goes.

| Mission row | Stamps | Type | Menu | Cost | Routine | Checked |
|---|---|---|---|---|---|---|
| (no row): mail | | mail | mail | none | claim_mail | owed: nothing left to collect on 2026-11-22 (toast) |
| Collect Factory products 1 time(s) in total | ? | idle claim | base | none | base_collect | owed: done by hand first |
| Complete 1 / 5 orders | ? + 1 | idle claim | base | none | base_collect | owed: 5 needs orders the Trading Post makes over the day |
| Interact with Operators in the Base and increase their Trust 5 / 10 time(s) | ? + ? | social check-in | base | none | base_collect | owed: done by hand first |
| Collect Credit from the Credit Store 1 time(s) | ? | idle claim | credit-store | none | claim_credit | owed: done by hand first |
| Clear any stage 1 / 4 / 8 time(s) | 1 + 2 + 2 | stamina sink | main-theme | 9 Sanity a run (1-12) | run_stage | yes, 2026-11-22 |
| Defeat a total of 1 / 3 enemy leaders in Main Story stages | 1 + 2 | stamina sink | main-theme | 9 Sanity a run (1-12, leader W) | run_stage | yes, 2026-11-22 |
| Defeat a total of 100 / 200 / 300 / 400 enemies | 1 + 1 + 2 + 2 | stamina sink | main-theme | 9 Sanity a run (1-12, 30 enemies): 14 runs, 126 Sanity | run_stage | yes, 2026-11-22 |

The routines' first runs on 2026-11-22 came after the hand pass, so the free rows' checks are owed to the next day's run. "?" is a multiplier never read: a finished row's Claim button covers it. On 2026-11-22 the 400-enemies tier was what completed the last set (009), so run_stage aims for it.

## Left out

- **Visit friends' Bases 1 time(s):** the account has no friends (Friends 0/100), and adding some means sending requests for the user.
- **Assign 1 Operators to restore Morale in the Dormitory:** assigning Durin (morale 24/24, free) to B104 didn't count. It likely needs an operator below full morale, taken off a shift, which reshuffles the user's base: team building.
- **Clear any stage using a Support Unit 1 times:** Auto Deploy replays a clear made without a support unit; a support unit means picking a friend's operator into a played squad.
- **Upgrade any Operator 1 time(s):** spends EXP cards and LMD on an operator the user picks.
- **Buy any items from the Credit Store 1 time(s):** spends credit on an item someone must pick; not tried yet. A candidate for a routine if the user names what to buy.
- **Use Recruitment 1 time(s):** a recruit (`core/notes/dailies.md`, Never automatic).
