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
12:03:43 INFO    lobby: start screen, handing over
12:03:43 DEBUG   start_screen: tap 1/3 at (960, 1036)
12:03:44 INFO    start_screen: left start screen, waiting for lobby
12:03:51 INFO    start_screen: in lobby
12:03:51 INFO    lobby: reached, waking HUD
12:03:52 DEBUG   nav: tap 1/5 at (1869, 49)
12:03:53 INFO    lobby: HUD showing
```

- Each module takes its logger with `log = logger(__file__)`, named after the file (`lobby`, `start_screen`, `nav`). That tells you which code wrote the line, so the message doesn't repeat it.
- The time shows how long each wait took, which matters because most failures in this bot are something taking longer than a timeout.
- `-7s` pads the level to `WARNING`'s width so the messages line up.
- Command-line entry points call `setup()` once. A normal run shows INFO and above. `--debug` adds the DEBUG lines (each tap and wait), for chasing a problem. A skill log (§5) always gets every level.

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
- **Returning False by design.** A routine that returns False so its caller can deal with the screen hasn't given up. That's INFO (e.g. start_screen's `popup open, returning to caller`, which the lobby routine then closes).
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
