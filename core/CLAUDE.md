# Core notes

`core/` is the code every game shares. Its notes live in `core/notes/`:

- `notes/UI.md`: menu behaviour two or more games show, and the Rules every routine and core's own screen checks follow. Imported here, so sessions that only touch `core/` load the Rules too.
- `notes/dailies.md`: the daily types the games share. Not imported: only the learn-dailies skill needs it, and reads it itself.

The loop from launch to a game's lobby is `core/lobby.py`, run from each game's spec in `<game>/routines/lobby.py`; how it works is in its docstring.

@notes/UI.md
