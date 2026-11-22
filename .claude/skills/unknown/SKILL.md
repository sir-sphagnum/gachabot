---
name: unknown
description: Go through the screens the bot saved as unknown (logs/unknown/, a capture nothing in a game's templates explained, saved before it pressed Back or gave up), work out what each one is, and patch the game's templates, spec, routines or notes so the bot knows it next time. Use when the user says "check unknown screens", "triage unknowns", "what did the bot not recognise", when a run logs `unknown screen:`, or after a run fails.
---

# Unknown screens

What gets saved, its fields and how sightings are counted: `.claude/logging.md` §9. Which kind of screen goes where: `core/notes/UI.md` and the map skill. This skill is the order to work in.

1. List them: `python -m core.unknown <game>` (or no game, for all). Nothing listed: tell the user and stop.
2. Before acting on a game, read `<game>/CLAUDE.md` and the notes it imports (project CLAUDE.md).
3. For each save, Read its PNG and its JSON (`doing`, `routine`, `uptime`, `count`, `closest`), then decide what it is:
   - **Wrong layout or a screen that moved:** the whole capture is scaled or shifted against the menu's saved `screen.png`, or a known identifier sits just under 0.85 in `closest`. Nothing is cut from it (`e7/notes/UI.md`, start-screen, Wrong layout). A layout gone wrong is fixed by a restart. Tell the user, and mark it done.
   - **A popup over any menu, or a first-of-the-day screen:** a common popup (common: First of the day or week), mapped with the map skill's popup step. Cut from this capture only if it is the game's normal layout.
   - **A dialog only the lobby opens:** a lobby state, added to the spec's `dialogs` in `<game>/routines/lobby.py` (new-game skill, step 5).
   - **A load or a launch screen:** `<game>/templates/common/loading/` (common: Loading screens). If it showed early in a launch (`uptime`) and has nothing fixed to match, raise the spec's `launch` instead.
   - **A screen that waits on the user's choice** (a download, an account): a stop screen (new-game skill, step 3). Ask the user what to choose there.
   - **A menu of the tree, not mapped yet:** the map skill.
   - **The game outside the bot's reach** (Android's home screen, another app, a sign-in page): tell the user, and mark it done. Signing in is the user's to do.
   When a save is ambiguous, show the user the capture and ask.
4. Map or patch it. Driving the game to see the screen live, or to test a fix, follows the project's rules on asking before using the emulator. Check what you cut with `python -m core.lobby <game> classify <the save>`: it should land in its new step, not `unknown`.
5. Write what was learnt in the game's notes, as the map skill says.
6. Mark each handled save: `python -m core.unknown <game> done <file>…`. Leave the ones still open, and tell the user which and why.
7. Don't commit. Offer the commit at the end of the user's request.
