# Arknights notes

Arknights's notes live in `ak/notes/`, one file per topic. Add to the matching file there rather than here.

- `notes/UI.md`: how each menu behaves (states, how to identify and switch them, quirks found while testing), one section per menu.
- `notes/dailies.md`: the daily missions, the routine that does each, and what it costs.
- `notes/routines.md`: named groups of routines (e.g. "daily routine") and what each runs.
- `../core/notes/UI.md`: menu behaviour shared with other games, which the notes above cite as "(common: <section>)".

`python -m core.nav ak goto <menu>` takes the game to any menu in `ak/templates/` reachable from the lobby (navigate skill).

@notes/UI.md
@notes/dailies.md
@notes/routines.md
@../core/notes/UI.md
