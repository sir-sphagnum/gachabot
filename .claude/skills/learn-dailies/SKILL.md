---
name: learn-dailies
description: Learn a game's dailies with Claude choosing the taps - survey its lobby, read its daily-missions list as the list of what to do, propose a plan for the user to approve, then map and write each free daily's routine without waiting for the user's clicks, check each against its mission row, and set up a next-day cold-start probe. Use after new-game, when the user says "learn dailies <game>", "learn <game>'s dailies", "work out the dailies", or similar.
---

# Learn dailies

In map and task the user decides every tap. Here Claude decides, from three sources: the game's own daily-missions list (what to do), `core/notes/dailies.md` (what each kind of daily looks like and which routine to start from) and the screen. The user approves the plan once, and each tap that can spend something. Everything is recorded with the map and task skills' tools, so the result is the same tree, notes and routines they make.

Run all commands from the project root.

## Before you start

- The game has a lobby and a `start_screen` routine (new-game skill). If not, run new-game first.
- Read `<game>/CLAUDE.md` and the notes it imports, `core/notes/dailies.md`, and the map and task skills (`.claude/skills/map/SKILL.md`, `.claude/skills/task/SKILL.md`): this skill uses their tools and their Stop steps.
- Open the log: `python -m core.log start learn-dailies` (on `(inside <skill>)` from another conversation: `python -m core.log end --all`, then start again). Check `python -m core.device health`, and again every ~30 taps: exploring captures a lot (common: BlueStacks memory). Over 18 GB, stop and ask to restart BlueStacks before the next tap: past ~22 GB screenshots come back blank mid-session.

## Rules for the taps you choose

- Every tap you choose yourself goes through `python -m tools.map click … --auto`. `--auto` refuses a button or menu named with a word that can spend (`core.tree.SPEND_WORDS`: buy, start, confirm, sweep, battle, refresh…), so **name each button after its label**, as the map skill says. Never rename one to get past the check.
- Before tapping, read the button's label and what's around it. A price, a currency icon, a stamina cost, a count that would go down, or a confirm dialog: don't tap. Put it in the plan (below) and wait for the user.
- Never tap anything under "Never automatic" in `core/notes/dailies.md`, even with `--auto` allowing it.
- Read a fresh capture before each tap (`python -m tools.map shot` when anything may have moved since the last one): a tap chosen from an old capture lands on whatever opened since. Read boxes off the full 1920x1080 capture or off `python -m tools.map sheet [CAPTURE...] [--box X Y W H]` (a grid labelled in device pixels), never off a preview you scaled yourself.
- Act on every warning `click` prints before the next tap: the screen didn't change (drop the line), it still shows HERE (the tap was a `--stay`, or a dialog to log as a state), HERE is no menu `finish` will know, or BlueStacks is over its memory limit.
- Come back from a menu with `python -m tools.map back`, never Back on the lobby itself (it opens the quit dialog: common: Lobbies).
- A dialog or popup you don't know: don't close it by guessing. Note it (`python -m tools.map note`) with your guess of its kind (map skill, popup or dialog), close it with its own close or Cancel if it has one, otherwise stop and ask.

The missions list says what to do, so it's read first and the lobby is explored only for what its rows leave open: exploring every lobby control first spends taps on menus that hold no daily (achievements, career, notification panels).

## 1. Survey the lobby

1. `python -m core.nav <game> goto lobby`, then `python -m tools.map start <game>`; Read the capture.
2. List every control you can see, with its label and box, and give each a guess from `core/notes/dailies.md`: missions, idle claim, limited attempts, stamina sink, social check-in, one of "Seen in one game", or nothing daily (settings, events, summon, shop). Show the list to the user in one message; don't wait for an answer unless something is unclear.
3. Find the missions menu (`core/notes/dailies.md`, Missions claim: the labels to look for). If the lobby has none, look one menu deep in the likeliest hub (a Menu or main-menu button). Then go to step 3 (read the missions list) before step 2.

## 2. Explore

After step 3, for each lobby control the missions rows point to that their Go buttons didn't reach, and each hub on a route a row needs, up to ~15:

1. `python -m tools.map click lobby <menu-name> X Y W H --auto`, the name taken from its label. Read the after-capture.
2. A new menu: `python -m tools.map leads <menu-name>` (`--after` once a load has passed, as in the task skill). Note in one line what it holds and which daily type it looks like. Look for the type's controls and its done signal (claim lit or grey, a count, a timer), and note them; don't tap them yet.
3. `python -m tools.map back`, and check the capture is the lobby again. If it isn't, try `back` once more, then note where it got stuck and `python -m core.nav <game> goto lobby`.

Go a level deeper only toward a daily (a hub that holds Campaign or Resource stages, a shop's tabs), never into a mode's Start.

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
| Clear 3 stages 0/3 | stamina sink | the-stage | 3 x 10 stamina | — (asked) | |
```

Cost is "none" or what one run spends, read from the screen.

Then choose the rows to propose:

1. Drop rows whose mode needs many decisions made by hand rather than an auto or sweep mode: building a team, picking a doll or upgrade, a fight with no way to finish it unplayed, a map whose route is chosen node by node. List them under "Left out" with the reason.
2. If the missions menu has an activity bar (points per row, chests at thresholds), the goal is its top chest, not every row: of the rows left, pick the cheapest set that reaches it, free rows first, then the cheapest paid ones. Rows past the goal go under "Left out" too.

Then ask the user, in one message: which of the paid rows to automate and how much each may spend, and whether any free row should be left alone. This is the only approval for free rows; each paid row needs its own yes, and its amount goes into the table. Wait for the answer.

## 5. Each free daily

For each approved row with cost "none", one at a time, run the task skill's flow with yourself as the user:

1. Task Start (its steps 2–6) with the task named after the routine (`claim-mail` → `claim_mail`). Navigate there with `python -m core.nav <game> goto <menu>` (map the route first if goto can't reach it).
2. Choose the steps from the type in `core/notes/dailies.md` and from what step 2 noted: the claim control while lit, its reward dialog's close, a tab to pick first. Tap each with `python -m tools.map click <menu> <button> X Y W H --stay --auto`, and say in one line what you tapped and what changed, as the task skill does.
3. The type says what a done screen looks like; capture one (it's usually the state right after the claim) and log the `info_` that tells it (`python -m tools.map info …`).
4. Task Stop (its steps 1–9), answering the questions it would ask the user yourself where the type's entry answers them ("not there means done" for a claim), and asking the user only what it doesn't. Start the routine from the file the type names. The approved plan answers Task Stop's step 7 for a free row: run it without asking.

A row that turns out to cost something after all (a confirm dialog with a price): stop that row, close the dialog with its Cancel, update its Cost in the table and ask.

## 6. Paid dailies

Never spend by hand while exploring. A daily allowance can't be redone the same day, so a spend made by hand leaves the routine with nothing to test until tomorrow.

For each paid row the user approved:

1. Map the route with `--auto` up to the spending control: the count to set, the dialogs before the spend, and the control that spends. Look at its label and the cost it shows, and log it with `info` instead of tapping it. The type's "Finishing a fight without playing it" table says what to look for near Start.
2. Task Stop as above (steps 1–6): `finish`, then write the routine. The spend is one tap, never retapped (doc_policy Rule 2's scope), and the routine sets the amount the user approved and checks it on screen before that tap.
3. Run the routine (`python -m <game>.bot <routine> --debug`): its first run is the spend and the test. The screens after the spend (a fight, a result dialog) aren't mapped yet, so the routine stops on the first one it doesn't know and saves it as its error screen. Map it from there (`tools.map start`, then `state` / `info` / its close), close it, finish the routine with it, and check the rest on the next day's run.

While a fight or load runs, write the next routine or the notes instead of waiting on it.

## 7. Check against the missions list

After each routine's first successful run (`python -m <game>.bot <routine>`), open the missions menu and read its row again:

- progress moved, or the row now shows Claim / complete: write "yes, <date>" in Checked;
- it didn't move: the routine returned True without doing the daily. Read its run with `--debug`, fix, run again;
- the row was already complete before the run: Checked stays empty, and the check is owed to the next day's run. Say so.

Then write `<game>/routines/claim_dailies.py` (the missions claim, from the file `core/notes/dailies.md` names) and a "daily routine" in `<game>/notes/routines.md`: every approved routine, then `claim_dailies` last, as one `python -m <game>.bot start lobby … claim_dailies` command.

## 8. Next day

First-of-the-day screens can only be met on the next day's first launch (common: First of the day or week), and no session will be waiting then. Offer a scheduled check:

1. Ask the user the game's daily reset time (local) and whether the PC and BlueStacks will be on then.
2. On their yes, create a scheduled task (`create_scheduled_task`) for ~15 minutes after reset, daily, with this prompt (fill in the game; it must stand on its own):

   > In the GachaBot project, run `python -m tools.probe <game> cold`. It force-stops <game>, launches it and runs its start_screen and lobby routines while recording the screen, then writes recon/probe/report.md. Read the report, then Read each capture it lists under "Screens nothing identifies". Reply with one line per unknown screen: what it shows and whether it looks like a popup over any menu or a dialog of the lobby (core/notes/UI.md, "First of the day or week"). Don't map, tap, close or commit anything: the user maps them with the map skill. If the probe says the health check failed, say so and stop.

3. Tell the user it runs while the Claude app is open (or at its next launch), and that its report lists the screens to map with the map skill (`tools.map popup` / `state`). Also suggest a `python -m tools.probe <game> walk` after their next mapping session: it checks every mapped menu is still reached and recognised.

## 9. Finish

Write each menu's section in `<game>/notes/UI.md` as the map and task skills say. Close the log (`python -m core.log end`), then commit and push (templates stay local; check the diff for anything personal). Tell the user which rows are automated and checked, which are owed a check, which wait on them, and the daily routine's command.
