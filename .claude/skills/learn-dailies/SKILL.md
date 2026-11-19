---
name: learn-dailies
description: Learn a game's dailies with Claude choosing the taps - survey its lobby, read its daily-missions list as the list of what to do, plan which rows to do and each one's steps before tapping any, then work each daily through the task skill's flow with Claude giving the steps (spending stamina where a daily needs it), write its routine, check each against its mission row, and set up a next-day cold-start probe. Use after new-game, when the user says "learn dailies <game>", "learn <game>'s dailies", "work out the dailies", or similar.
---

# Learn dailies

In map and task the user decides every tap. Here Claude decides, from three sources: the game's own daily-missions list (what to do), `core/notes/dailies.md` (what each kind of daily looks like and which routine to start from) and the screen. It first plans which dailies to do and writes each one's steps as a user would give them to the task skill (§4), then works them through the task flow in the user's place (§5). Stamina (the game's refilling energy, under whatever name the lobby's notes give it) is spent where a planned daily needs it without asking; anything else that spends waits for the user's word. Everything is recorded with the map and task skills' tools, so the result is the same tree, notes and routines they make.

Run all commands from the project root.

## Before you start

- The game has a lobby and a `start_screen` routine (new-game skill). If not, run new-game first.
- Read `<game>/CLAUDE.md` and the notes it imports, `core/notes/dailies.md`, and the map and task skills (`.claude/skills/map/SKILL.md`, `.claude/skills/task/SKILL.md`): this skill uses their tools and their Stop steps.
- Open the log: `python -m core.log start learn-dailies` (on `(inside <skill>)` from another conversation: `python -m core.log end --all`, then start again). Check `python -m core.device health` (common: BlueStacks memory), and again every ~30 taps: exploring captures a lot. On any other failure, tell the user what it says and wait.

## Rules for the taps you choose

- Every tap you choose yourself goes through `python -m tools.map click … --auto`. `--auto` refuses a button or menu named with a word that can spend (`core.tree.SPEND_WORDS`: buy, start, confirm, sweep, battle, refresh…), so **name each button after its label**, as the map skill says. Never rename one to get past the check.
- Before tapping, read the button's label and what's around it. A price, a currency icon, a stamina cost, a count that would go down, or a confirm dialog: don't tap it while exploring (§1–§3). A spend is tapped only as a step of a planned row (§5): stamina without asking, any other cost once the user approves its row.
- Never tap anything under "Never automatic" in `core/notes/dailies.md`, even with `--auto` allowing it.
- Read a fresh capture before each tap (`python -m tools.map shot` when anything may have moved since the last one): a tap chosen from an old capture lands on whatever opened since. Read boxes off the full 1920x1080 capture or off `python -m tools.map sheet [CAPTURE...] [--box X Y W H]` (a grid labelled in device pixels), never off a preview you scaled yourself.
- Act on every warning `click` prints before the next tap: the screen didn't change (drop the line), it still shows HERE (the tap was a `--stay`, or a dialog to log as a state), HERE is no menu `finish` will know, or BlueStacks is over its memory limit.
- Come back from a menu with `python -m tools.map back`, never Back on the lobby itself (it opens the quit dialog: common: Lobbies).
- A dialog or popup you don't know: don't close it by guessing. Note it (`python -m tools.map note`) with your guess of its kind (map skill, popup or dialog), close it with its own close or Cancel if it has one, otherwise stop and ask.

The missions list says what to do, so it's read first and the lobby is explored only for what its rows leave open: exploring every lobby control first spends taps on menus that hold no daily (achievements, career, notification panels).

## 1. Survey the lobby

1. `python -m core.nav <game> goto lobby`, then `python -m tools.map start <game>`; Read the capture.
2. List every control you can see, with its label and box, and give each a guess from `core/notes/dailies.md`: missions, idle claim, limited attempts, stamina sink, social check-in, one of "Seen in one game", or nothing daily (settings, events, summon, shop). Show the list to the user in one message; don't wait for an answer unless something is unclear.
3. Find the missions menu (`core/notes/dailies.md`, Missions claim: the labels to look for). It is often an unlabelled icon (a clipboard, a checklist) or a strip that shows the current task, with neighbours that look alike: a notification panel, achievements (lifetime goals), a career or story-progress list. Tell them apart by what opens: the missions menu has a Daily tab or section, rows with n/m progress, and usually an activity bar with chests. If the lobby has none, look one menu deep in the likeliest hub (a Menu or main-menu button). Then go to step 3 (read the missions list) before step 2.
4. Find the mailbox as `core/notes/dailies.md`, Mail says. new-game maps it; if `<game>/templates/` has no `mail` menu, map it now as new-game's Mailbox bullet says. Every game gets a `claim_mail` routine, whether or not a missions row asks for mail.

## 2. Explore

After step 3, for each lobby control the missions rows point to that their Go buttons didn't reach, and each hub on a route a row needs, up to ~15:

1. `python -m tools.map click lobby <menu-name> X Y W H --auto`, the name taken from its label. Read the after-capture.
2. A new menu: `python -m tools.map leads <menu-name>` (`--after` once a load has passed, as in the task skill). Note in one line what it holds and which daily type it looks like. Look for the type's controls and its done signal (claim lit or grey, a count, a timer), and note them; don't tap them yet.
3. `python -m tools.map back`, and check the capture is the lobby again. If it isn't, try `back` once more (some screens ignore Back: common: Back), then note where it got stuck and `python -m core.nav <game> goto lobby`.

Go a level deeper only toward a daily (a hub that holds Campaign or Resource stages, a shop's tabs), never into a mode's Start.

A hub's cards or a list's entries can sit past the screen edge. Swipe to find them, and note the swipe that brings each one on screen (common: Lists that move).

## 3. Read the missions list

1. Open the missions menu (map it the same way). Pick its daily tab or section (common: Daily missions: it may open on another).
2. Read every row: its words, progress (n/m), reward, and whether it has a Go / Shortcut. Scroll the list if it continues (`python -m core.input swipe X1 Y1 X2 Y2`, then `python -m tools.map shot`); log each scroll position as a note.
3. For each row with a Go button whose menu you haven't seen: tap it with `--auto` (`python -m tools.map click missions go-<row> X Y W H --auto`), `leads` the menu it opens, and `back`. The Go button is the same art on every row and its row moves as rows complete, so it only shows where a daily lives. The route the bot walks is mapped from the lobby, not through Go.
4. Open the missions menu a second time later in the session (after a claim, or after leaving with a row finished): it may open on another tab or sub-tab once rewards are waiting or one was used last, and its identifiers and the routine's tab picks must cover each.
5. Close the session the way the map skill's Stop does (its steps 1–5: `log`, an identifier for each new menu, `finish`, fixing what it flags, the notes; leave this skill's log open): the task flow below starts its own session, which wipes `recon/map/`. The identifiers are yours to pick; ask only where no element sets a menu apart.

## 4. The plan

Write `<game>/notes/dailies.md` (create it, and add `@notes/dailies.md` to `<game>/CLAUDE.md`'s imports and a line for it to its list of notes):

```markdown
# <Game> dailies

The daily missions as the game lists them, the routine that does each, and what it costs. learn-dailies made it; `<game>/notes/routines.md` has the command that runs them in order.

| Mission row | Type | Menu | Cost | Routine | Checked |
|---|---|---|---|---|---|
| Claim mail 0/1 | mail | mail | none | claim_mail | yes, 2026-11-18 |
| Clear 3 stages 0/3 | stamina sink | the-stage | 3 x 10 stamina | the_stage | |
```

Cost is "none" or what one run spends, read from the screen.

If no missions row names mail, add a row for it anyway ("(no row): mail", §1 step 4).

Then choose the rows to propose:

1. Drop rows whose mode needs many decisions made by hand rather than an auto or sweep mode: building a team, upgrading an item or unit, a fight with no way to finish it unplayed, a map whose route is chosen node by node. List them under "Left out" with the reason.
2. If the missions menu has an activity bar (points per row, chests at thresholds), the goal is its top chest, not every row: of the rows left, pick the cheapest set that reaches it, free rows first, then the cheapest paid ones. Rows past the goal go under "Left out" too.

Then write each chosen row's steps the way a user would give them in the task skill: the menu to go to, each tap in order (a tab, a stage, a count to set, the claim or the spend, the dialogs after it), and the screen that shows it's done. Take them from the row's type in `core/notes/dailies.md` (for a fight, its "Finishing a fight without playing it" table) and from what §2 and §3 noted. A screen not seen yet, such as what follows a spend, is written as what you expect and marked as a guess.

Show the user the table and each row's steps in one message before tapping any of them. Keep the steps out of the notes: once worked, the routine holds them.

Rows paid only in stamina need no approval: plan what the rows need (the amount goes into the table), as long as the stamina on hand covers it. Rows paid in anything else (a daily attempt, tickets, materials) are asked about in that same message, with what each would spend; wait for that answer only for those rows and carry on with the rest meanwhile. Never-automatic spends (premium currency, refills) stay out whatever the plan says.

## 5. Each daily

Work the planned rows one at a time, free ones first, through the task skill's flow with yourself as the user. Doing a daily by hand first maps every screen it shows, those after a spend included, before its routine is written. The price: an allowance the hand pass uses up can't be redone the same day, so the routine's spend is checked on the next day's run (§6).

1. Task Start (its steps 2–6) with the task named after the routine (`claim-mail` → `claim_mail`). Navigate there with `python -m core.nav <game> goto <menu>` (map the route first if goto can't reach it).
2. Give yourself the row's planned steps one at a time, as task steps. Tap each with `python -m tools.map click <menu> <button> X Y W H --stay --auto` (`leads` for one that opens a menu), and say in one line what you tapped and what changed, as the task skill does. For the spending step, check on a fresh capture that the cost and count it shows match the plan, then tap it without `--auto` (which refuses it). Log the screens after it (a fight, a result dialog) as the task skill's step 5 says. While a fight or load runs, write notes instead of waiting on it.
3. A step that doesn't go as planned (its control isn't there, a screen the plan didn't expect, a price on a row planned free): stop the row and close any priced dialog with its Cancel. Fix the row's steps and Cost in the plan; carry on if the cost is stamina, otherwise ask about the row.
4. The type says what a done screen looks like; capture one (usually the state right after the claim or the spend) and log the `info_` that tells it (`python -m tools.map info …`). Then check the row moved: `python -m core.nav <game> goto <missions menu>` and Read a `python -m tools.map shot`. If it didn't, a step missed the daily: find which before Stop.
5. Task Stop (its steps 1–9), answering the questions it would ask the user yourself where the type's entry answers them ("not there means done" for a claim), and asking the user only what it doesn't. Start the routine from the file the type names. A claim whose reward is a common popup is tapped as common: Reward dialogs says. A spend is one tap, never retapped (Rule 2's scope, `core/notes/UI.md`): the routine sets the planned amount and checks it on screen before that tap, and when the stamina left buys fewer runs than planned, it runs what it can rather than failing. The approved plan answers Task Stop's step 7: run the routine without asking. When the hand pass used up the day's allowance, that run can only find the done state (Rule 6) and must return True from it.

## 6. Check against the missions list

After each routine's first successful run (`python -m <game>.bot <routine>`), open the missions menu and read its row again:

- progress moved, or the row now shows Claim / complete: write "yes, <date>" in Checked;
- it didn't move although the daily could still be done: the routine returned True without doing it. Read its run with `--debug`, fix, run again;
- the day's allowance was used up (by the hand pass or earlier play), or the row was complete before the run: Checked stays empty, and the check is owed to the next day's run. Say so.

Before writing `claim_dailies`, make sure §3 step 4 was done: a `claim_dailies` written from one visit fails the first time the menu opens elsewhere.

Then write `<game>/routines/claim_dailies.py` (the missions claim, from the file `core/notes/dailies.md` names) and a "daily routine" in `<game>/notes/routines.md`: `claim_mail` first and `claim_dailies` last (`core/notes/dailies.md`, Mail and Missions claim), with every other approved routine between them, as one `python -m <game>.bot start lobby claim_mail … claim_dailies` command.

## 7. Next day

First-of-the-day screens can only be met on the next day's first launch (common: First of the day or week), and no session will be waiting then. Offer a scheduled check:

1. Ask the user the game's daily reset time (local) and whether the PC and BlueStacks will be on then.
2. On their yes, create a scheduled task (`create_scheduled_task`) for ~15 minutes after reset, daily, with this prompt (fill in the game; it must stand on its own):

   > In the GachaBot project, run `python -m tools.probe <game> cold`. It force-stops <game>, launches it and runs its start_screen and lobby routines while recording the screen, then writes recon/probe/report.md. Read the report, then Read each capture it lists under "Screens nothing identifies". Reply with one line per unknown screen: what it shows and whether it looks like a popup over any menu or a dialog of the lobby (core/notes/UI.md, "First of the day or week"). Don't map, tap, close or commit anything: the user maps them with the map skill. If the probe says the health check failed, say so and stop.

3. Tell the user it runs while the Claude app is open (or at its next launch), and that its report lists the screens to map with the map skill (`tools.map popup` / `state`). Also suggest a `python -m tools.probe <game> walk` after their next mapping session: it checks every mapped menu is still reached and recognised.

## 8. Finish

Write each menu's section in `<game>/notes/UI.md` as the map and task skills say. Close the log (`python -m core.log end`). Don't commit: check the diff for anything personal (templates stay local), then offer the commit and push, and commit only on the user's yes.

Then report inline, tersely: a short table of the rows (automated and checked, owed a check, left out), what was spent, the daily routine's command, and what waits on the user, in a few lines with no narrative. End by asking whether they want a more detailed rundown (time taken, steps, decisions, mistakes); write it only on their yes.
