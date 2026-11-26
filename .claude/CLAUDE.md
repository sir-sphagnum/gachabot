# GachaBot

Each game's notes live in `<game>/notes/`, one file per topic. Menu notes go in `<game>/notes/UI.md` (e.g. `e7/notes/UI.md`), one section per menu. `<game>/CLAUDE.md` points to these files and imports them (`@notes/UI.md`). Claude Code loads it on its own once a session reads files under the game's folder, so only sessions working on that game pay for its notes. When you learn how a menu behaves (its states, how to identify or switch them, quirks found while testing), add it to that game's `notes/UI.md`. For a new game, create `<game>/notes/UI.md` and a `<game>/CLAUDE.md` that imports it. Behaviour that a second game shows too moves to `core/notes/UI.md`, which every `<game>/CLAUDE.md` and `core/CLAUDE.md` also import; the game's notes keep their own numbers and cite it as "(common: <section>)".

If you're about to act on a game (tap, run a routine, map menus) before having read anything under its folder, read `<game>/CLAUDE.md` and the notes it imports first.

The bot drives Waydroid while its session runs (`waydroid show-full-ui` starts it), else the Android Studio emulator (AVD `Gaming`), over the SDK's adb (`core/adb.py`, `connect`). `python -m …` in skills and notes means the project's venv: run `.venv/bin/python -m …` (set up with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).

Screens the bot met and nothing in a game's templates explained are saved in `logs/unknown/<game>/` (`python -m core.unknown` lists them). The unknown skill works through them.

## Rules

Where text belongs, when it may be deleted, and how lessons become rules: @doc_policy.md

- Always write paths relative to the project root (e.g. `e7/routines/lobby.py`), never absolute ones (`C:\...`), in code, docs, notes, memory and commit messages. Absolute paths expose the user's folder names.
- Never keep outdated information in memory, notes or code docs (docstrings, comments, `notes/*.md`). When something changes, rewrite the text to describe only how things are now, and put what changed and why in the git commit message.
- Before adding or changing a log message, or choosing between logging and printing, read `.claude/logging.md`.
