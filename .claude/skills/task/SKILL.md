---
name: task
description: Work a menu's controls (claim, collect, switch tabs, confirm) step by step as the user directs, then turn the steps into a routine the bot can rerun. Navigate and map get the game to a menu; task acts inside it. Use when the user says "task <name>", "start task <name>", "new task", or names a task to run such as "claim forest".
---

# Task

Navigate and map find a menu. A task does something in it: the user names the controls to tap, one step at a time, and you record each step. At the end the steps become a routine, `<game>/routines/<task>.py`, so the bot can rerun the task on its own (`python -m <game>.bot <task>`).

Run all commands from the project root.

## The images

A task's controls are buttons, saved like any other in the folder of the menu they sit on (map skill's scheme). A button that keeps the game on its menu (claim, tab, close a dialog) is named after itself: `btn_<menu>_<button>_<x>-<y>-<w>-<h>.png`. Such buttons never identify their menu and are no step in a route (`core.nav`), because many show only in some states (a claim button only while there is something to claim). A state the routine must check is an `info_`.

## Start: "task <name>"

1. If you haven't read anything under the game's folder this session, read `<game>/CLAUDE.md` and the notes it imports first.
2. Name the task: short, lowercase, hyphenated (`claim-forest`). Its routine module uses underscores (`claim_forest`), since Python names can't hold hyphens.
3. Open this run's log: `python -m core.log start task`. If it says `(inside <skill>)` and you didn't start that skill in this conversation, run `python -m core.log end --all`, then start again (`.claude/logging.md` §5).
4. Get to the task's menu:
   - **The user says to go there first**: follow the navigate skill (its log nests inside this one). Not in the tree: offer to map it (map skill).
   - **The user says the game is already there**: check it. Capture with `python -m core.input screenshot recon/task.png` and match the menu's identifying images (`python -m core.vision find <image> recon/task.png X Y W H`). If none match, say so and ask.
5. Start the step log: `python -m tools.map start <game>`. It wipes `recon/map/` and captures the screen; Read the path it prints.
6. Tell the user which menu you're on and that you're waiting for the task's steps.

## A step: "tap <control>", "claim <thing>"

1. Look at the current capture (the one the last `tools.map` command printed). Run `python -m tools.map shot` first when the screen may have changed since.
2. Find the control the user named. If you can't, or more than one thing fits, ask. Do not guess.
3. Box it in 1920x1080 pixels, tight but whole (label or icon), leaving out sparkles and other animated bits.
4. Tap and capture: `python -m tools.map click <menu> <button> X Y W H --stay`. Add `--fresh` when the control may have moved or changed since the capture (timers, a list that scrolls).
5. Read the after-capture and tell the user in one line: "tapped <control> (cx, cy) → <what changed>". If the screen shows:
   - **no change**: say so and ask whether to retry. Remove the useless line from `recon/map/log.jsonl`.
   - **another menu**: drop `"stay": true` from its line in `recon/map/log.jsonl` and set its `"name"` to the new menu's name, so `finish` makes the menu (map skill).
   - **a dialog or reward window over the menu**: ask the user whether it's a state of this menu (this action always opens it) or a popup that can show anywhere, and follow the map skill's "popup or dialog" rules. A dialog the task must answer gets an `info_` that identifies it (or a button that only shows on it) and a button for the tap that answers or closes it.
6. Ask the user what the routine should do when the control isn't there (nothing to claim yet, already claimed), unless they said. Log the answer with `python -m tools.map note <text>`. For a claim, "not there" usually means done, not a failure.

Anything the routine must check before or after a step ("only when the timer shows Done", "the count is now 3/3") is an `info_`: `python -m tools.map info <menu> <element> X Y W H`. Anything else worth keeping, log as a note.

Only tap what the user asked for. If a step would spend premium currency, make a purchase, or use up something limited the user didn't mention (stamina, a daily attempt), ask first.

## Stop: "end task" / "save task"

1. Run `python -m tools.map log` and check it with the user's steps in mind: right names, no taps that did nothing.
2. Run `python -m tools.map finish`. It crops each `btn_` and `info_` image into its menu's folder and checks it, as in the map skill. Fix any crop it flags.
3. `finish` only checks images against other menus. Also score each one on every capture of this session (`recon/map/*.png`, with `core.vision.find`): a control must match where the routine should tap it and not where it shouldn't (claimed, grey, under a dialog). Matching is blind to brightness, so a lit and a greyed-out button can score alike; tell those apart by colour in the routine instead. One image can serve several rows of a list when they share a layout: search it at each row's offset.
4. Write `<game>/routines/<task>.py` with `run()`, following `e7/routines/start_screen.py` and `.claude/logging.md`:
   - first `core.nav.goto(GAME, <menu>)`; return False if it fails;
   - then each step with `core.nav.tap_until(<button image>, <what shows after>)`, which closes the game's common popups before trusting a match (Rule 1). A step whose control may legitimately be missing checks for it first (`core.nav.locate`) and skips it at INFO;
   - True once the last step's result shows.
   Register it in `<game>/routines/__init__.py`'s `ROUTINES` under its module name.
5. Ask before running it: a rerun repeats the task, and a claim already taken leaves nothing to tap. If the user agrees, run `python -m <game>.bot <task> --debug` and report how it went.
6. Write what you learned about the menu's controls into its section of `<game>/notes/UI.md` (which state each shows in, what each tap leads to, scores), and how to run the task.
7. Close the log with `python -m core.log end`. Tell the user the routine's command, the notes that changed and the log file `end` printed.

## Running an existing task

When the user asks for a task that already has a routine (`ROUTINES` in `<game>/routines/__init__.py`), open the log (`python -m core.log start task`), run `python -m <game>.bot <task>`, report the outcome, and close the log. On a failure, capture the screen, Read it, and tell the user where it stopped.
