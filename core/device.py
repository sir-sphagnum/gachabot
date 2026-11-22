"""The BlueStacks device: which app is in focus, fullscreen, starting/stopping apps.

Usage: python -m core.device connect
       python -m core.device focus
       python -m core.device fullscreen
       python -m core.device health      exits 1 when BlueStacks needs a restart
                                         or Windows is low on memory
       python -m core.device restart [game ...]
           closes the running apps, then BlueStacks, opens it again and waits
           for Android to boot, then starts the games given (none if no game
           is given) one after another, each closing the one before, and runs
           each one's start_screen and lobby routines, if it has them, so each
           ends in its lobby; the last one is left running. While a game's
           lobby isn't reached, with no stop screen, load or popup showing
           (stuck_on), it restarts again, up to RESTART_TRIES in all
       python -m core.device start game
           closes every other running game in GAMES, then starts this one
       python -m core.device stop|status [game ...]
           no game means every game in GAMES
       game is a short name from GAMES (e.g. e7) or a package name.
"""

import ctypes
import glob
import importlib
import re
import subprocess
import sys
import time

from core.adb import AdbTimeout, adb, connect, player_pids, run
from core.input import BlankScreen, capture, tap
from core.log import logger, setup

log = logger(__file__)

# Short game names -> Android package names. The short name is also the game's
# package in this repo, which holds its templates/ (e.g. e7/templates/). The package
# names are the games' real Android IDs and can't be renamed.
GAMES = {
    "e7": "com.stove.epic7.google",
    "chaoszero": "com.smilegate.chaoszero.stove.google",
    "re1999": "com.bluepoch.m.en.reverse1999",
    "ba": "com.nexon.bluearchive",
    "ak": "com.YoStarEN.Arknights",
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
# Lines end in \r\n on some adb connections (seen after a BlueStacks restart).
FLOATING = re.compile(r"Task\{\S+ #(\d+) type=standard A=\d+:(\S+) [^}]*?visible=true [^}]*?mode=freeform"
                      r"[^}]*\}\s*mBounds=Rect\((\d+), (\d+)")

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


def uptime(game):
    """Seconds since the game's process started, or None if it isn't running.
    Reads ps's ETIME: [[DD-]HH:]MM:SS."""
    pid = adb("shell", "pidof", package(game)).split()
    if not pid:
        return None
    etime = adb("shell", "ps", "-o", "ETIME=", "-p", pid[0]).strip()
    m = re.fullmatch(r"(?:(?:(\d+)-)?(\d+):)?(\d+):(\d+)", etime)
    if not m:
        return None
    days, hours, minutes, seconds = (int(v or 0) for v in m.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


def start_game(game, timeout=30):
    """Launch a game (or bring it to the front if it's already running),
    after closing every other game in GAMES that is running.

    Waits until it is the app in focus, then fullscreens it: templates are cut
    from the fullscreen screen, so nothing matches in a floating window.
    Returns True on success, False if another game didn't stop, the game
    didn't come to the front within `timeout` seconds, or it stayed floating.
    """
    pkg = package(game)
    others = [p for p in running_apps() if p in GAMES.values() and p != pkg]
    if others:
        ok, _ = close_apps(others)
        log.info(f"closed {', '.join(others)}" if ok else f"not all of {', '.join(others)} stopped")
        if not ok:
            return False
    # The launcher activity, e.g. "com.stove.epic7.google/kr.supercreative.epic7.AppActivity".
    # Looked up rather than hard-coded, since a game update can rename it.
    component = adb("shell", "cmd", "package", "resolve-activity", "--brief",
                    "-c", "android.intent.category.LAUNCHER", pkg).splitlines()[-1]
    if "/" not in component:
        raise ValueError(f"{pkg} is not installed or has no launcher activity")
    adb("shell", "am", "start", "-n", component)
    if not wait_until(lambda: (focused_app() or ("",))[0] == pkg, timeout, interval=0.5):
        return False
    return fullscreen()


def stop_game(game, timeout=10):
    """Force-stop a game. Returns True once its process is gone."""
    pkg = package(game)
    adb("shell", "am", "force-stop", pkg)
    return bool(wait_until(lambda: not is_running(pkg), timeout, interval=0.5))


def running_apps():
    """Packages of the installed (non-system) apps that have a process running."""
    installed = [line.split(":", 1)[1] for line in adb("shell", "pm", "list", "packages", "-3").splitlines()
                 if line.startswith("package:")]
    procs = adb("shell", "ps", "-A", "-o", "NAME").split()
    return [p for p in installed if any(n == p or n.startswith(p + ":") for n in procs)]


# Seconds the apps get in the background before they are force-stopped. Going
# home first gives them Android's pause/stop callbacks, where an app saves and
# closes what it has open; a force-stop or a killed BlueStacks gives them none.
BACKGROUND_WAIT = 3


def close_apps(apps=None):
    """(ok, packages): send the apps home, then force-stop each. `apps` is a
    list of packages; None means every running app. ok is False if one of
    them is still running."""
    apps = running_apps() if apps is None else apps
    if not apps:
        return True, []
    adb("shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(BACKGROUND_WAIT)
    stopped = [stop_game(app) for app in apps]
    return all(stopped), apps


# --- health -----------------------------------------------------------------

# BlueStacks' own memory grows while the bot captures the screen (9.6 GB to
# 22 GB in ~45 min with two processes capturing every second). At 22 GB
# every screencap came back empty; at 27 GB Windows ran out of memory and
# adb couldn't start. Both cleared only with a BlueStacks restart.
PLAYER_MAX_GB = 18
FREE_MIN_GB = 4  # Windows' free commit space (RAM plus page file)


def health():
    """(ok, message): whether BlueStacks' memory and Windows' free memory
    leave room for a long run."""
    free = _free_commit_gb()
    player = player_gb()
    if player is None:
        return False, "BlueStacks isn't running"
    problems = []
    if player > PLAYER_MAX_GB:
        problems.append(f"BlueStacks uses {player:.1f} GB (over {PLAYER_MAX_GB}): "
                        "restart it (python -m core.device restart)")
    if free < FREE_MIN_GB:
        problems.append(f"only {free:.1f} GB of memory free (under {FREE_MIN_GB}): close other apps")
    if problems:
        return False, "; ".join(problems)
    return True, f"OK: BlueStacks uses {player:.1f} GB, {free:.1f} GB free"


def player_gb():
    """Memory BlueStacks' emulator has committed, in GB, or None if it isn't running."""
    sizes = [_commit_gb(int(pid)) for pid in player_pids()]
    return max(sizes) if sizes else None


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class _ProcessMemory(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def _free_commit_gb():
    status = _MemoryStatus(dwLength=ctypes.sizeof(_MemoryStatus))
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.ullAvailPageFile / 2**30


def _commit_gb(pid):
    """Memory process `pid` has committed (its private bytes), in GB."""
    query = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    handle = ctypes.windll.kernel32.OpenProcess(query, False, pid)
    if not handle:
        return 0.0
    try:
        counters = _ProcessMemory(cb=ctypes.sizeof(_ProcessMemory))
        ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        return counters.PagefileUsage / 2**30
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


# --- restarting BlueStacks --------------------------------------------------

CLOSE_TIMEOUT = 15   # seconds for BlueStacks to be gone after it is forced closed
BOOT_TIMEOUT = 120   # seconds from opening BlueStacks to Android having booted
# The arguments of BlueStacks' own "BlueStacks Desktop" shortcut. With
# `--instance <name>` instead, HD-Player opened only a tooltip window and
# Android never booted.
PLAYER_ARGS = ["--guest", "--present=embed", "--chrome=windows"]
# A game can come up after a restart laid out for another screen size, where
# nothing matches, and a further restart sets it right (e7/notes/UI.md,
# start-screen, Wrong layout). So a lobby missed after a restart is retried
# with another restart, this many in all.
RESTART_TRIES = 3


def restart(boot_timeout=BOOT_TIMEOUT):
    """(ok, message): close the running apps, close BlueStacks, open it again,
    and wait until Android has booted and adb answers. Frees the memory
    BlueStacks builds up while the bot captures the screen. Games are not
    started."""
    player = _player_exe()
    if player_pids():
        _close_apps_before_restart()
    if not _close_player():
        return False, "BlueStacks still open after closing it"
    connect.cache_clear()  # the cached serial belongs to the closed BlueStacks
    # Detached, so BlueStacks outlives this process.
    subprocess.Popen([player, *PLAYER_ARGS],
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)
    log.info("closed, opening")
    if not wait_until(_booted, boot_timeout, interval=2):
        return False, f"BlueStacks not booted {boot_timeout}s after opening it"
    return True, "BlueStacks restarted"


def with_room(game, routine):
    """Run routine() with BlueStacks' memory kept in check, and return its
    result (False when a restart failed).

    Before it: when BlueStacks is over PLAYER_MAX_GB, restart it and bring
    `game` back to its lobby. During it: if it stops on blank screenshots
    (core.input.BlankScreen) or on ADB not answering (core.adb.AdbTimeout,
    seen at 19.5 GB when a cold start pushed it past the limit mid-routine),
    do the same and run it once more. A rerun is safe because routines start
    by going to their menu from wherever the game is and read what is left
    to do from the screen. One daily routine alone grew BlueStacks by up to
    ~7 GB, so the check runs before each.
    """
    player = player_gb()
    if player is not None and player > PLAYER_MAX_GB:
        log.info(f"BlueStacks uses {player:.1f} GB (over {PLAYER_MAX_GB}), restarting it first")
        if not _restart_with(game):
            return False
    try:
        return routine()
    except (BlankScreen, AdbTimeout) as e:
        log.warning(f"{e}: restarting BlueStacks and running it again")
    if not _restart_with(game):
        return False
    return routine()


def _restart_with(game, tries=RESTART_TRIES):
    """Restart BlueStacks, start `game` and take it to its lobby, restarting
    again while the lobby isn't reached, `tries` restarts in all. True on
    success."""
    for attempt in range(1, tries + 1):
        ok, msg = restart()
        (log.info if ok else log.error)(msg)
        if not ok or not start_game(game):
            log.error(f"{game} not started after the restart")
            return False
        if run_to_lobby(game) is not False:
            return True
        seen = stuck_on(game)
        if seen:
            log.error(f"{game} stuck on {seen}, not restarting again")
            return False
        log.warning(f"{game} lobby not reached after restart {attempt}/{tries}")
    log.error(f"{game} lobby not reached after {tries} restarts")
    return False


STUCK_LOOK = 3  # seconds stuck_on looks; ak's pre-start diamond drops out of single captures


def stuck_on(game, look=STUCK_LOOK):
    """What `game` is waiting on, as a few words ("popup pre-start"): a stop
    screen, a loading screen or a common popup seen within `look` seconds;
    None when none of them shows.

    Restarting again when the lobby isn't reached is for a game that came up
    wrong (e7's wrong layout and its Login and Select Server screens,
    e7/notes/UI.md), which restarts set right. One of these screens means
    the game is up and waiting on something a restart doesn't answer, and a
    restart can do harm: on 2026-11-22 two of them, with ak blocked under a
    launch dialog over pre-start, killed its launch update, and it asked to
    download 13 GB again. Menus don't count: e7's start-screen identifier
    matched at 0.98 behind Login on 2026-11-21, when restarts fixed it."""
    from core import nav  # core.nav imports this module

    def known():
        try:
            screen = capture()
        except (BlankScreen, AdbTimeout):
            return None
        stop = nav.stop_screen(game, screen)
        if stop:
            return f"stop screen {stop}"
        if nav.loading(game, screen):
            return "a loading screen"
        popup = nav.open_popup(nav.game_popups(game), screen)
        return f"popup {popup}" if popup else None

    return wait_until(known, look)


def run_to_lobby(game):
    """Run the game's start_screen routine, then its lobby routine (their
    <game>.routines ROUTINES entries), and return the last one's result, or
    None when the game has neither. `game` is a short name from GAMES; a
    package name has no routines here.

    The lobby routine runs whatever start_screen returned: start_screen
    leaves any popup open after START (a game's first launch of the day
    shows several) for the lobby routine to close, and fails only when it
    could not get past the start screen. From the lobby, lobby returns at
    once."""
    if game not in GAMES:
        return None
    module = f"{game}.routines"
    try:
        routines = importlib.import_module(module).ROUTINES
    except ModuleNotFoundError as e:
        if e.name not in (game, module):  # the routines exist but import something missing
            raise
        return None
    result = None
    for name in ("start_screen", "lobby"):
        if name in routines:
            result = routines[name]()
            log.info(f"{game} {name}: {'ok' if result else 'not done'}")
    return result


def _close_apps_before_restart():
    """Close the apps, logging what happened. Never stops the restart: a
    BlueStacks that needs restarting may not answer adb."""
    try:
        ok, apps = close_apps()
    except RuntimeError as e:  # includes AdbTimeout
        log.warning(f"apps not closed: {e}, closing BlueStacks anyway")
        return
    if not ok:
        log.warning(f"not all of {', '.join(apps)} stopped, closing BlueStacks anyway")
    elif apps:
        log.info(f"closed {', '.join(apps)}")


def _player_exe():
    paths = glob.glob(r"C:\Program Files\BlueStacks*\HD-Player.exe")
    if not paths:
        raise RuntimeError("HD-Player.exe not found. Is BlueStacks installed?")
    return paths[0]


def _close_player(timeout=CLOSE_TIMEOUT):
    """Force-close every HD-Player.exe. Returns True once none is left.

    Forced straight away: asked to close (taskkill without /F), BlueStacks
    stayed open every time. It booted normally after each forced close."""
    for pid in player_pids():
        run("taskkill", "/F", "/PID", pid)
    return bool(wait_until(lambda: not player_pids(), timeout, interval=0.5))


def _booted():
    try:
        return adb("shell", "getprop", "sys.boot_completed") == "1"
    except RuntimeError:  # not listening yet (AdbTimeout is a RuntimeError too)
        connect.cache_clear()
        return False


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
    elif cmd == "health":
        ok, msg = health()
        _answer(msg, ok)
        sys.exit(0 if ok else 1)
    elif cmd == "restart":
        before = player_gb()
        for attempt in range(1, RESTART_TRIES + 1):
            ok, msg = restart()
            if ok:
                was = f"{before:.1f} GB before" if before is not None else "wasn't running"
                msg += f": {was}, {player_gb():.1f} GB now"
            _answer(msg, ok)
            missed = stuck = False
            for game in args if ok else []:
                started = start_game(game)
                ok &= started
                _answer(f"{game}: {'started' if started else 'failed to start'}", started)
                passed = run_to_lobby(game) if started else None
                if passed is not None:
                    ok &= passed
                    missed |= not passed
                    _answer(f"{game}: {'in lobby' if passed else 'lobby not reached'}", passed)
                seen = stuck_on(game) if passed is False else None
                if seen:
                    stuck = True
                    _answer(f"{game}: stuck on {seen}, not restarting again", False)
            if not missed or stuck or attempt == RESTART_TRIES:
                break
            print(f"Restarting again ({attempt + 1}/{RESTART_TRIES})")
            before = player_gb()
        sys.exit(0 if ok else 1)
    elif cmd == "start":
        if len(args) != 1:
            sys.exit("start takes one game: starting it closes the others")
        ok = start_game(args[0])
        _answer(f"{args[0]}: {'started' if ok else 'failed to start'}", ok)
        sys.exit(0 if ok else 1)
    elif cmd in ("stop", "status"):
        for game in args or list(GAMES):
            if cmd == "stop":
                ok = stop_game(game)
                _answer(f"{game}: {'stopped' if ok else 'still running'}", ok)
            else:
                _answer(f"{game}: {'running' if is_running(game) else 'stopped'}")
    else:
        sys.exit(__doc__)
