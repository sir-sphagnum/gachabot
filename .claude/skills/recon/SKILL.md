---
name: recon
description: Record the BlueStacks screen to the recon/ folder (one screenshot per second) and click buttons on request, taking a screenshot after each click. Use when the user says "begin recon", "start recon", "start recording", or similar.
---

# Recon

Records what happens in BlueStacks while the user asks you to click through the game. All screenshots go in `recon/` at the project root.

## Start

1. Open this run's log, from the project root:
   ```
   python -m core.log start recon
   ```
   It prints the log file. If it says `(inside <skill>)` and you didn't start that skill in this conversation, an earlier run never ended: run `python -m core.log end --all`, then start again (`.claude/logging.md` §5).
2. Check `python -m core.device health`. If it fails, tell the user what it says (restart BlueStacks, close apps) and wait for them.
3. Start the capture loop in the background (run_in_background: true), from the project root:
   ```
   python -m tools.recon
   ```
   It takes a screenshot every second and saves it as `recon/YYYYMMDD-HHMMSS.png` only if it differs from the last one saved (more than 1% of pixels changed; see `core/vision.py`), until it is stopped. While a routine runs alongside it for a long time, add `--interval 3`: both capturing every second grew BlueStacks' memory until its screenshots came back empty. If it errors right away (BlueStacks not running, ADB off), report the error and stop. A capture that fails later is printed as `Capture failed: …` and retried after a growing pause; if the user asks how it's going and the output shows those, say so and suggest `python -m core.device health`.
4. Tell the user recon is running and that they can ask you to click things.

## When the user asks to click a button

1. Take a fresh screenshot so you see the current screen:
   ```
   python -m core.input screenshot recon/current.png
   ```
   Then Read `recon/current.png`.
2. Find the button the user named. If you can't find it, or more than one thing matches, say so and ask. Do not guess.
3. Work out the center of the button in device pixels. The screen is 1920x1080; if the image you see is shown at a different size, scale the coordinates to 1920x1080.
4. Tap it:
   ```
   python -m core.input tap X Y
   ```
5. Wait about 1 second for the screen to react, then take the after-click screenshot, named for the click:
   ```
   python -m core.input screenshot recon/click-YYYYMMDD-HHMMSS-<button-name>.png
   ```
   Use the current time and a short lowercase, hyphenated button name (e.g. `click-20261109-201530-summon.png`).
6. Read the after-click screenshot and tell the user in a line what you clicked (name and coordinates) and what the screen shows now.

Only click what the user asked for. If a click would spend premium currency or make a purchase and the user did not clearly say to, ask first.

## Stop

When the user says "end recon", "stop recon", or similar: stop the background `tools.recon` task, delete `recon/current.png`, then close the log with `python -m core.log end`. Run `python -m tools.recon --summary` and report what it prints (how many screenshots `recon/` holds and their size) and the log file `end` printed. When it's over ~1 GB, offer to delete the older recordings; delete only on the user's yes.

## Notes

- Screenshots are about 2 MB each. Near-duplicates are skipped, so a still screen costs nothing, but heavily animated screens (battles, summons) may still save one every capture.
