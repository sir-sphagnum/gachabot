# Logging rules

How routines and navigation report what they are doing: what logs and what prints, the line format, which level a message gets, and how to word it. Read before adding or changing a log message.

## 1. Log or print

- **Log** (Python `logging`, set up by `core/log.py`): routines (`<game>/routines/`), `core/nav.py`, and the per-command `ok`/`failed` lines of `<game>/bot.py`. Their output is a running record of a bot run, read afterwards to see what happened and when.
- **Print**: a command's answer. That means usage text, the results of `core/*` and `tools/*` command lines (`Tapped (x, y)`, `Saved …`, `Found …`), the tree listing and its Problems list. The answer is read as is, and a timestamp and level in front of it only get in the way.
- **Both**: a command that prints its answer and acts on the game or files (tap, back, screenshot, start/stop, find, crop, each `tools.map` and `tools.recon` step) also logs what it did, so a skill log (§5) records it. It calls `setup(console=False)`: the line goes to the skill log only, never the terminal, where it would repeat the answer. Read-only listings (`core.tree`, `core.nav routes`, `tools.map log`) don't log.

## 2. Line format

```
%(asctime)s %(levelname)-7s %(name)s: %(message)s     datefmt %H:%M:%S
```

```
12:03:40 DEBUG   nav: black screen, waiting
12:03:41 WARNING lobby: popup_disconnected open, closing
12:03:41 DEBUG   nav: popup_disconnected: close tap 1/5 at (960, 688)
12:03:43 INFO    lobby: start screen, tapping START (1/9)
12:03:43 DEBUG   lobby: START at (960, 1036)
12:03:45 INFO    lobby: left start screen, waiting for the lobby
12:03:52 INFO    lobby: lobby idle, waking HUD
12:03:52 DEBUG   nav: tap 1/3 at (1869, 49)
12:03:53 DEBUG   lobby: lobby showing, watching 4s for popups
12:03:57 INFO    lobby: reached
```

- Each module takes its logger with `log = logger(__file__)`, named after the file (`lobby`, `unknown`, `nav`). That tells you which code wrote the line, so the message doesn't repeat it.
- The time shows how long each wait took, which matters because most failures in this bot are something taking longer than a timeout.
- `-7s` pads the level to `WARNING`'s width so the messages line up.
- Command-line entry points call `setup()` once. A normal run shows INFO and above. `--debug` adds the DEBUG lines (each tap and wait), for chasing a problem. A skill log (§5) and a run log (§7) always get every level.

## 3. Levels

Ask these in order and take the first yes:

| Question | Level | Examples |
|---|---|---|
| Does a routine give up here (return False)? A routine is a `<game>/routines/` module, `goto`, or a bot command. | **ERROR** | `lobby: not reached after 10 backs`, `nav: shop not reached after 2 attempts` |
| Did something get in the way that the code is now working around, or did a helper fail (see below)? | **WARNING** | `popup_disconnected open, closing`, `tap 2/5 skipped: btn_x.png not on screen`, `lobby not reached, restarting walk` |
| Is it a state reached, a hand-over, a plan, or success? | **INFO** | `reached, waking HUD`, `start screen, handing over`, `route: lobby > shop`, `on shop` |
| Otherwise: a single action or a wait | **DEBUG** | `tap 2/5 at (1869, 49)`, `back 3/10`, `black screen, waiting` |

**Helpers and routines.** The helpers in `core/nav.py` (`tap_until`, `close_popup`, `past_black`) never log ERROR. They hand their result to a routine, which decides what it means. When a helper fails, it logs why at WARNING, because only the helper knows which of its reasons it was. The routine then logs its ERROR naming what it didn't reach, without repeating the reason:

```
WARNING nav: expected element not seen in 5 tries
ERROR   lobby: HUD not shown
```

Edge cases:

- **Retried routines.** A routine that gives up still logs its ERROR even when its caller retries it. The caller's WARNING then says what it does next (`lobby not reached, restarting walk`).
- **Same event, different outcome.** The level follows what happens next, not the event. In `goto`, `no route from here to shop` is a WARNING when it goes on to walk from the lobby. `no route from lobby to shop` is an ERROR, because the walk stops.
- **Returning False by design.** A routine that returns False so its caller can deal with the screen hasn't given up. That's INFO, not ERROR.
- **Every give-up logs.** A routine that returns False without an ERROR leaves the log ending mid-run with no reason.

## 4. Wording

- **Shape:** `subject: outcome`, or a short verb phrase. `back 3/10`, `reached, waking HUD`, `popup_disconnected: close tap 1/5 at (x, y)`.
- **Lowercase start, no final period.** This is the GNU and Go convention for program messages: each line is an entry, not a sentence.
- **No narration.** Join what is happening and what comes next with `, ` and one short verb (`closing`, `waiting`, `handing over`, `restarting walk`), not `; now doing X`.
- **Don't repeat the logger name.** In `lobby`'s own lines, write `reached`, not `in lobby`.
- **Names:**
  - Popups get a `popup_` prefix on their key: `popup_disconnected`, `popup_date-changed`, `popup_quit`. A space reads as prose ("popup disconnected" sounds like a disconnection).
  - Menus are named by their folder name as is (`shop`, `lobby`).
  - Templates are named by file name (`btn_shop.png`).
- **Numbers:** counts as `n/max` (`tap 2/5`), durations as `30s`, points as `(x, y)`.
- **Failures** say what wasn't reached and, when the routine knows it, after how much: `not reached after 10 backs`, `no lobby 30s after start screen`.
- **Warnings** end with what the code does about it (`…, closing`, `…, restarting walk`), unless nothing follows and an ERROR comes next.

## 5. Skill logs

Each skill run (recon, map, navigate) keeps its log lines in one file, `logs/YYYYMMDD-HHMMSS-<skill>.log` (gitignored). The skill opens it with `python -m core.log start <skill>` and closes it with `python -m core.log end`. While it's open, every process that calls `setup()` also appends its lines there, at every level. A run spans many processes (a background recon loop, one process per tap or map step), so a pointer file, `logs/current`, tells each of them where to write.

- **Nesting.** A skill started while another's log is open writes into that log (`navigate started, inside recon`), and its `end` leaves the log open for the outer skill. Lines from both land in one file, interleaved in time order, which is what a run that mixes them needs.
- **A log left open.** If a run never reached `end`, the next `start` nests inside it and says `(inside <skill>)`. When that skill isn't one you started in this conversation, run `python -m core.log end --all` and start again.
- **End after the loop stops.** A background process that is still running keeps writing to the file it opened, even after `end`. Stop the recon loop before closing its log.

## 6. Error screens

Every process that calls `setup()` saves the emulator screen on each ERROR line as `logs/YYYYMMDD-HHMMSS-error-<logger>.png` (gitignored), and logs `error screen: <path>` at INFO right after it. An ERROR is a routine giving up (§3), and the screen it gave up on is what explains why; a capture taken later may show the game has moved on. One capture per 5 s per process, since a routine's ERROR and the bot's `failed` line that follows it show the same screen. If the capture itself fails (emulator down), a WARNING says so and the ERROR stands alone.

To watch a run that takes minutes (a `<game>.bot` run, `core.device restart`, a cold start), so a failure reaches you while it runs and not when it exits (Rule 7, `core/notes/UI.md`): start it with the Bash tool's background option, its output going to a file, then watch that file with the Monitor tool (`timeout_ms` 1800000). Read the error screen only when one is logged. An `unknown screen:` WARNING names a capture nothing explained, saved before the bot acted on it (§9): it is the screen to map, where the error screen may show what came after.

```bash
python -m <game>.bot <routine>... > logs/watch-<game>.txt 2>&1          # Bash, background
tail -n +1 -f logs/watch-<game>.txt | grep --line-buffered -E "WARNING|ERROR|error screen|Traceback|^  |Error"   # Monitor
```

- **Why a file.** A Monitor kills its command when it expires (30 minutes at most), and `run_stage` alone runs ~25 minutes. Under the Monitor only `tail` dies; the run goes on. Re-arm with `tail -n 0 -f`, which skips the lines already seen.
- **Why this filter.** Every line that passes is a message in the conversation, and a Monitor that passes too many is stopped. INFO (each `route:`, each `on <menu>`) is left out, since the background run's exit notification already says how it ended; only its `error screen:` line passes, as it names the ERROR's capture. WARNING is kept because a run working around something (`popup_x open, closing` again and again) is the early sign of an ERROR. `^  ` and `Error` let a crash's traceback through whole (its `  File` lines and the exception), not just its first line.
- **When the run exits,** stop the Monitor (TaskStop): `tail -f` never ends by itself.
- **No Monitor** for a command that ends itself on its result (`python -m core.nav <game> wait`), or a short run in the foreground: its exit is the one notification needed.

## 7. Run logs

Every routine run writes all its lines, DEBUG included, to `logs/YYYYMMDD-HHMMSS-<run>.log` (gitignored). The file is kept only when the run goes wrong and deleted when it exits cleanly. A run goes wrong when it logs an ERROR (a routine giving up, §3), crashes, or is stopped with Ctrl+C. A failed run's log tells the whole story even without `--debug`. Successful runs leave nothing behind, so `logs/` holds only runs worth reading. A run that fails prints `run log: <path>` as its last line, next to the `error screen:` line (§6).

- **Which runs.** Entry points that run a routine pass `setup(run=<name>)`. `<game>/bot.py` names the run after itself and its arguments (`e7.bot-lobby-hunt`). A routine's own `__main__` passes `__spec__.name` (`e7.routines.lobby`). `core.nav` passes one for `goto` and `tap`. Commands that only answer or act once (`core.input`, `core.device`, `tools.*`) don't, and a new routine's `__main__` copies the line from an existing one.
- **Crashes.** An uncaught exception is logged as an ERROR (`run: crashed`) with its traceback, not printed by Python's default hook. That puts the traceback in the run log and saves its error screen, and the terminal still shows it through the console handler.
- **Killed outright.** The file is written as the run goes, not buffered. A process that is killed (task manager, a closed terminal) keeps its log, ending wherever it stopped.
- **With a skill log open.** The run's lines go to both the skill log (§5) and its run log. The skill log keeps everything, and the run log stays only if the run failed.

## 8. Step statistics

Every call of `tap_until`, `close_popup` and `held` (`core/nav.py`) adds one JSON line to `logs/steps.jsonl` (gitignored), from every game and process, whether the run succeeds or fails. Run logs (§7) keep only failed runs, so this file is the only record of steps that needed help on runs that still went through. `python -m tools.steps` ranks the steps by how often they needed it.

```
{"t": "2026-11-16T17:32:41", "run": "e7.bot-run_arena", "game": "e7", "routine": "run_arena",
 "kind": "tap_until", "button": "btn_arena_arena-team_….png", "expected": ["…"],
 "found": "…", "taps": 2, "skipped": 1, "popups": 0, "s": 2.9, "ok": true}
```

- **Who.** `run` is the name `setup(run=…)` was given (None outside a routine run). `routine` is the file stem of the first caller outside `core/`, so steps `goto` takes are counted under the routine that called `goto`; `core` means core's own command line. `game` comes from the template paths, else from the calling routine's folder.
- **Names.** `button` is the template's file name, `popup_<name>` for `close_popup`, a check's function name for `held` (or an `expected` check). Points and lambdas have no name, so they're `x,y@routine:line` and `check@routine:line`; editing the routine moves the line and starts a new row.
- **Counts.** `taps` made, `skipped` (of them, taps on a button not on screen), `popups` closed on the way (`tap_until` only), `flickers` (`held` only: times the result showed and dropped), `s` seconds the call took, popups included, and `ok` whether it returned a result. A `close_popup` inside a `tap_until` writes its own line too.
- **Never in the way.** A line that can't be written logs a WARNING and the step goes on. The file is appended to, never rotated: about 250 bytes a line, ~25 KB per full daily. Delete it to start the counts over.

## 9. Unknown screens

A screen that nothing in a game's templates explains (`core.nav.describe` is empty: not black, no stop, load, popup or menu) is saved by `core.unknown` as `logs/unknown/<game>/YYYYMMDD-HHMMSS-<routine>.png` (gitignored), with a `.json` beside it, before the bot acts on it. The lobby loop (`core.lobby`) saves one before each Back it presses on it, or when a launch or START wait ends on it. `tap_until`, `wait_clear` and `clear` save the screen they gave up on, when it is unknown. Claude reads them with the unknown skill.

- **Fields.** `game`, `run` and `routine` as in §8, `first` and `last` seen, `count`, `doing` (what the bot did next: `pressing back 3/10`, `giving up`) and `last_doing`, the game's `uptime` in seconds, and `closest`: the five `info_` images that scored best on it. A known identifier just under 0.85 there points at a screen that moved or a wrong layout, not a new screen.
- **Once per screen.** A capture within 1 % of a saved one (`core.vision.difference`, the scale `tools.dedupe` uses) only counts up that save's `count`. The line is a WARNING the first time a process sees the screen and DEBUG after, so ten Backs on it log one WARNING.
- **Kept until handled.** Saves stay across runs until `python -m core.unknown <game> done <file>…` deletes them, once mapped or judged not worth mapping.
- **Never in the way.** A save that fails logs a WARNING and the caller goes on.
