"""Create the files every game package needs (new-game skill, part 1).

Usage: python -m tools.new_game GAME PACKAGE [--title TITLE]

GAME is the game's short name, lowercase (e.g. e7): it becomes the folder
<game>/ and a Python package, so it must be a valid identifier and can't shadow
a module Python already has. PACKAGE is its Android package name
(e.g. com.stove.epic7.google). TITLE is the game's name as the files
should write it (e.g. "Reverse: 1999"); without it, GAME in capitals when
it's 3 letters or fewer (E7), else GAME title-cased.

Adds GAME to core.device.GAMES (unless it is already there with PACKAGE) and
creates:

    <game>/__init__.py, bot.py, config.py
    <game>/routines/__init__.py         ROUTINES, empty
    <game>/templates/.gitkeep           keeps the git-ignored folder in the repo
    <game>/templates/common/popups/
    <game>/notes/UI.md, routines.md
    <game>/CLAUDE.md                    imports the notes

It refuses to touch a game folder that already exists. The start_screen and
lobby routines aren't created: they depend on the game's screens, which the
rest of the skill maps first. A stub lobby routine returning True would let
core.nav walk from a lobby it never checked.
"""

import keyword
import re
import sys

from core import ROOT
from core.log import logger, setup

log = logger(__file__)

NAME = re.compile(r"[a-z][a-z0-9_]*")
PACKAGE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+")
DEVICE = ROOT / "core" / "device.py"
# The GAMES dict in core/device.py, up to its closing brace.
GAMES_BLOCK = re.compile(r"^GAMES = \{\n(.*?)^\}", re.M | re.S)

FILES = {
    "__init__.py": '''\
"""{title} bot: routines and logic that only apply to {title}. Builds on core/; core never imports this."""
''',
    "config.py": '''\
"""{title} settings shared by the bot and its routines."""

from core import templates_dir
from core.device import package

GAME = "{game}"{pad}# key in core.device.GAMES and this package's name
PACKAGE = package(GAME)      # Android package name
TEMPLATES_DIR = templates_dir(GAME)  # {game}/templates/

# The key that closes the current menu: Android Back.
BACK_KEY = "back"
''',
    "bot.py": '''\
"""{title} bot entry point.

Usage: python -m {game}.bot start          launch {title} (or bring it to the front), fullscreen
       python -m {game}.bot stop           force-stop {title}
       python -m {game}.bot back           close the current menu
       python -m {game}.bot ROUTINE ...    run routines from {game}.routines.ROUTINES, in order

Add --debug to also log each tap and wait.
"""

import sys

from core import device
from core.input import back as press_back
from core.log import logger, setup
from {game}.config import BACK_KEY, GAME
from {game}.routines import ROUTINES

log = logger(__file__)


def start():
    """Launch {title} fullscreen. Returns True once it is in focus and fullscreen."""
    return device.start_game(GAME, fullscreen=True)


def stop():
    return device.stop_game(GAME)


def back():
    """Close the current menu (BACK_KEY; see {game}.config)."""
    press_back(BACK_KEY)


COMMANDS = {{"start": start, "stop": stop, "back": back}}


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if a != "--debug"]
    setup(debug="--debug" in sys.argv[1:])
    unknown = [n for n in names if n not in COMMANDS and n not in ROUTINES]
    if not names or unknown:
        if unknown:
            print(f"Unknown: {{', '.join(unknown)}}")
        print(__doc__)
        print("Routines:", ", ".join(ROUTINES) or "(none yet)")
        sys.exit(1)
    for name in names:
        result = (COMMANDS.get(name) or ROUTINES[name])()
        if result is False:
            log.error(f"{{name}}: failed")
            sys.exit(1)
        log.info(f"{{name}}: ok")
''',
    "routines/__init__.py": '''\
"""{title} routines, one module each.

A routine module exposes run() and is registered in ROUTINES so {game}.bot can
run it by name, e.g.:

    # {game}/routines/arena.py
    def run(): ...

    # here
    from {game}.routines import arena
    ROUTINES = {{"arena": arena.run}}

core.device restart runs the "start_screen" and "lobby" entries after
starting the game, and core.nav loads {game}/routines/lobby.py by name, so
keep both names.
"""

ROUTINES = {{}}
''',
    "templates/.gitkeep": "",
    "notes/UI.md": '''\
# {title} UI notes

How {title} menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `{game}/templates/` (see the map skill for the scheme). `{game}/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `{game}/`.
''',
    "notes/routines.md": '''\
# {title} routines

Named groups of routines the user asks for by one name. Each routine is in `{game}/routines/` and registered in `{game}.routines.ROUTINES`.
''',
    "CLAUDE.md": '''\
# {title} notes

{title}'s notes live in `{game}/notes/`, one file per topic. Add to the matching file there rather than here.

- `notes/UI.md`: how each menu behaves (states, how to identify and switch them, quirks found while testing), one section per menu.
- `notes/routines.md`: named groups of routines (e.g. "daily routine") and what each runs.

`python -m core.nav {game} goto <menu>` takes the game to any menu in `{game}/templates/` reachable from the lobby (navigate skill).

@notes/UI.md
@notes/routines.md
''',
}


def check_name(game):
    """None if `game` can be a game package, else why not."""
    if not NAME.fullmatch(game) or keyword.iskeyword(game):
        return f"{game!r} is not a lowercase Python identifier"
    if game in sys.stdlib_module_names or game in sys.builtin_module_names:
        return f"{game!r} would shadow Python's own {game} module"
    if (ROOT / game).exists():
        return f"{game}/ already exists"
    return None


def add_to_games(game, package):
    """Add `game` to core.device.GAMES. Returns None, or why it can't."""
    text = DEVICE.read_text(encoding="utf-8")
    block = GAMES_BLOCK.search(text)
    if not block:
        return "GAMES dict not found in core/device.py"
    entries = dict(re.findall(r'^\s+"([^"]+)":\s*"([^"]+)",', block.group(1), re.M))
    if game in entries:
        if entries[game] != package:
            return f"core.device.GAMES has {game} as {entries[game]}, not {package}"
        return None
    if package in entries.values():
        other = next(k for k, v in entries.items() if v == package)
        return f"{package} is already in core.device.GAMES as {other}"
    end = block.end() - 1  # the closing brace
    DEVICE.write_text(text[:end] + f'    "{game}": "{package}",\n' + text[end:], encoding="utf-8")
    return None


def create(game, package, title=None):
    """Create the game's package. Returns (ok, message)."""
    problem = check_name(game) or (None if PACKAGE.fullmatch(package)
                                   else f"{package!r} is not an Android package name")
    if problem:
        return False, problem
    problem = add_to_games(game, package)
    if problem:
        return False, problem
    if not title:
        title = game.upper() if len(game) <= 3 else game.replace("_", " ").title()
    pad = " " * max(1, 20 - len(game))  # lines GAME's comment up with PACKAGE's
    base = ROOT / game
    for rel, body in FILES.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.format(game=game, title=title, pad=pad), encoding="utf-8")
    (base / "templates" / "common" / "popups").mkdir(parents=True)
    log.info(f"created {game}/ for {package}")
    return True, f"Created {game}/ ({package}); in core.device.GAMES as {game}"


if __name__ == "__main__":
    args = sys.argv[1:]
    title = None
    if "--title" in args:
        i = args.index("--title")
        title = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    if len(args) != 2 or title == "":
        print(__doc__)
        sys.exit(1)
    setup(console=False)
    ok, message = create(*args, title)
    print(message)
    sys.exit(0 if ok else 1)
