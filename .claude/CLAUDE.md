# GachaBot

Each game's notes live in `<game>/notes/`, one file per topic. Menu notes go in `<game>/notes/UI.md` (e.g. `e7/notes/UI.md`), one section per menu. `<game>/CLAUDE.md` points to these files and imports them (`@notes/UI.md`). Claude Code loads it on its own once a session reads files under the game's folder, so only sessions working on that game pay for its notes. When you learn how a menu behaves (its states, how to identify or switch them, quirks found while testing), add it to that game's `notes/UI.md`. For a new game, create `<game>/notes/UI.md` and a `<game>/CLAUDE.md` that imports it.

If you're about to act on a game (tap, run a routine, pathfind) before having read anything under its folder, read `<game>/CLAUDE.md` and the notes it imports first.
