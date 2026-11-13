"""The BlueStacks device: which app is in focus, fullscreen, starting/stopping apps.

Usage: python -m core.device connect
       python -m core.device focus
       python -m core.device fullscreen
       python -m core.device start|stop|status [--fullscreen] [game ...]
           game is a short name from GAMES (e.g. e7) or a package name;
           no game means every game in GAMES. --fullscreen applies to start.
"""

import re
import sys
import time

from core.adb import adb, connect
from core.input import tap
from core.log import logger, setup

log = logger(__file__)

# Short game names -> Android package names. The short name is also the game's
# package in this repo, which holds its templates/ (e.g. e7/templates/). The package
# names are the games' real Android IDs and can't be renamed.
GAMES = {
    "e7": "com.stove.epic7.google",
    "chaoszero": "com.smilegate.chaoszero.stove.google",
    "reverse1999": "com.bluepoch.m.en.reverse1999",
}


def wait_until(condition, timeout, interval=0.2):
    """Call condition() until it returns something truthy or `timeout` seconds
    pass. Returns that truthy result, or None on timeout. A numpy array (a
    capture) counts as truthy: its own truth value raises."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = condition()
        if result is not None if hasattr(result, "shape") else result:
            return result
        if interval:
            time.sleep(interval)
    return None


# --- focus ------------------------------------------------------------------


def focused_app():
    """Return (package, activity) of the window in focus, or None if nothing is.

    Reads e.g. "mCurrentFocus=Window{20e3607 u0 com.stove.epic7.google/...MainActivity}".
    """
    # Plain `dumpsys window`: the `windows` subsection omits mCurrentFocus here.
    windows = adb("shell", "dumpsys", "window")
    match = re.search(r"mCurrentFocus=Window\{\S+ \S+ ([^/\s}]+)/([^\s}]+)\}", windows)
    if not match:
        return None
    package, activity = match[1], match[2]
    if activity.startswith("."):
        activity = package + activity
    return package, activity


# --- fullscreen -------------------------------------------------------------

# A visible floating app task and its bounds, e.g.
#   * Task{5dd1090 #45 type=standard A=10118:com.stove.epic7.google U=0 ... visible=true ... mode=freeform ...}
#     mBounds=Rect(269, 113 - 1651, 890)
FLOATING = re.compile(r"Task\{\S+ #(\d+) type=standard A=\d+:(\S+) [^}]*?visible=true [^}]*?mode=freeform"
                      r"[^}]*\}\n\s*mBounds=Rect\((\d+), (\d+)")

# BlueStacks window-menu taps, relative to the floating window's top-left corner.
ARROW = (75, 23)             # down arrow in the title bar: opens the window menu
FULLSCREEN_ICON = (49, 131)  # first icon in the menu
# dumpsys reports the task fullscreen before the screen shows it: captures
# still showed the floating window 0.5 s later and the fullscreen game at 1.3 s.
FULLSCREEN_DRAW = 1.5        # seconds


def floating_window():
    """(task_id, left, top) of the focused app if it is floating, else None."""
    focus = focused_app()
    if not focus:
        return None
    tasks = adb("shell", "dumpsys", "activity", "activities")
    for task, package, left, top in FLOATING.findall(tasks):
        if package == focus[0]:
            return task, int(left), int(top)
    return None


def menu_open(task):
    """True while the window menu (the one with the Fullscreen icon) is showing.

    The menu has no window of its own in `dumpsys window`, but SurfaceFlinger
    lists a "Handle menu of task=<id>" layer while it is up.
    """
    return f"Handle menu of task={task}#" in adb("shell", "dumpsys", "SurfaceFlinger", "--list")


def fullscreen(attempts=3, timeout=5):
    """Fullscreen the focused app. Returns True once it isn't floating and the
    screen shows it fullscreen.

    Waits for the menu to actually appear before tapping Fullscreen (a slow,
    still-loading game can take over a second), checks the result, and retries.
    """
    for _ in range(attempts):
        window = floating_window()
        if not window:
            return True
        task, left, top = window
        if not menu_open(task):
            tap(left + ARROW[0], top + ARROW[1])
            if not wait_until(lambda: menu_open(task), timeout):
                continue
            time.sleep(0.5)  # the layer appears before the open animation finishes
        tap(left + FULLSCREEN_ICON[0], top + FULLSCREEN_ICON[1])
        if wait_until(lambda: not _floating(task), timeout):
            time.sleep(FULLSCREEN_DRAW)
            return True
    return False


make_fullscreen = fullscreen  # for start_game, whose `fullscreen` argument hides this


def _floating(task):
    """Whether this task is still a visible floating window."""
    tasks = adb("shell", "dumpsys", "activity", "activities")
    return any(t == task for t, *_ in FLOATING.findall(tasks))


# --- starting and stopping games --------------------------------------------


def package(game):
    """Package name for a short name from GAMES, or a package name as given."""
    return GAMES.get(game, game)


def is_running(game):
    return bool(adb("shell", "pidof", package(game)))


def start_game(game, fullscreen=False, timeout=30):
    """Launch a game (or bring it to the front if it's already running).

    Waits until it is the app in focus, then fullscreens it if asked. Returns
    True on success, False if it didn't come to the front within `timeout`
    seconds or (with fullscreen=True) stayed floating.
    """
    pkg = package(game)
    # The launcher activity, e.g. "com.stove.epic7.google/kr.supercreative.epic7.AppActivity".
    # Looked up rather than hard-coded, since a game update can rename it.
    component = adb("shell", "cmd", "package", "resolve-activity", "--brief",
                    "-c", "android.intent.category.LAUNCHER", pkg).splitlines()[-1]
    if "/" not in component:
        raise ValueError(f"{pkg} is not installed or has no launcher activity")
    adb("shell", "am", "start", "-n", component)
    if not wait_until(lambda: (focused_app() or ("",))[0] == pkg, timeout, interval=0.5):
        return False
    return make_fullscreen() if fullscreen else True


def stop_game(game, timeout=10):
    """Force-stop a game. Returns True once its process is gone."""
    pkg = package(game)
    adb("shell", "am", "force-stop", pkg)
    return bool(wait_until(lambda: not is_running(pkg), timeout, interval=0.5))


def _answer(msg, ok=True):
    """Print the command's answer and log it, as ERROR when it failed."""
    print(msg)
    (log.info if ok else log.error)(msg[0].lower() + msg[1:])


if __name__ == "__main__":
    setup(console=False)
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else (None, [])
    if cmd == "connect":
        _answer(f"Connected to {connect()[1]}")
    elif cmd == "focus":
        focus = focused_app()
        _answer(f"{focus[0]}  ({focus[1]})" if focus else "Nothing in focus")
    elif cmd == "fullscreen":
        ok = fullscreen()
        _answer("Fullscreen" if ok else "Still floating", ok)
    elif cmd in ("start", "stop", "status"):
        full = "--fullscreen" in args
        for game in [a for a in args if a != "--fullscreen"] or list(GAMES):
            if cmd == "start":
                ok = start_game(game, fullscreen=full)
                _answer(f"{game}: {'started' if ok else 'failed to start'}", ok)
            elif cmd == "stop":
                ok = stop_game(game)
                _answer(f"{game}: {'stopped' if ok else 'still running'}", ok)
            else:
                _answer(f"{game}: {'running' if is_running(game) else 'stopped'}")
    else:
        sys.exit(__doc__)
