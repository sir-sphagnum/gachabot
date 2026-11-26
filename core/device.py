"""The Android the bot runs on (Waydroid while its session runs, else the
Android Studio emulator; core.adb.connect): which app is in focus,
starting/stopping apps, restarting the device.

Usage: python -m core.device connect
       python -m core.device focus
       python -m core.device health      exits 1 when the emulator needs a restart
                                         or the PC is low on memory
       python -m core.device restart [game ...]
           closes the running apps, then the device (Waydroid's session,
           or the emulator if only it is running), boots it again (or just
           starts it if it wasn't running) and waits for Android, then
           starts the games given (none if no game is given) one after
           another, each closing the one before, and runs
           each one's lobby routine, if it has one, so each ends in its
           lobby; the last one is left running. While a game's
           lobby isn't reached, with no stop screen, load or popup showing
           (stuck_on), it restarts again, up to RESTART_TRIES in all
       python -m core.device start game
           closes every other running game in GAMES, then starts this one
       python -m core.device stop|status [game ...]
           no game means every game in GAMES
       game is a short name from GAMES (e.g. e7) or a package name.
"""

import importlib
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from core.adb import AdbTimeout, adb, connect, run, sdk, waydroid_ip
from core.input import BlankScreen, capture
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
    "nc": "com.sunborn.neuralcloud.en",
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

    Waits until it is the app in focus. Returns True on success, False if
    another game didn't stop or the game didn't come to the front within
    `timeout` seconds.
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
    return bool(wait_until(lambda: (focused_app() or ("",))[0] == pkg, timeout, interval=0.5))


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
# closes what it has open; a force-stop or a killed emulator gives them none.
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

# The emulator's guest RAM is the AVD's hw.ramSize (8 GB for Gaming), and its
# qemu process holds that plus the GPU's memory and its own. Past this limit
# it holds more than that explains. A guess until a long run's `health` lines
# show how it grows.
EMULATOR_MAX_GB = 12
FREE_MIN_GB = 4  # the PC's available memory (MemAvailable)
EMULATOR_PROCESS = "qemu-system-x86"  # qemu-system-x86_64, cut to 15 characters by the kernel


def health():
    """(ok, message): whether the emulator's memory and the PC's free memory
    leave room for a long run. On Waydroid only the PC's free memory is
    checked: its Android shares the PC's kernel, with no qemu process to
    measure."""
    free = _available_gb()
    used = None if on_waydroid() else emulator_gb()
    if used is None and not on_waydroid():
        return False, "Neither Waydroid nor the emulator is running"
    problems = []
    if used is not None and used > EMULATOR_MAX_GB:
        problems.append(f"Emulator uses {used:.1f} GB (over {EMULATOR_MAX_GB}): "
                        "restart it (python -m core.device restart)")
    if free < FREE_MIN_GB:
        problems.append(f"only {free:.1f} GB of memory free (under {FREE_MIN_GB}): close other apps")
    if problems:
        return False, "; ".join(problems)
    device = "Waydroid" if used is None else f"emulator uses {used:.1f} GB"
    return True, f"OK: {device}, {free:.1f} GB free"


def emulator_pids():
    """Process IDs of the running emulator (its qemu process)."""
    return [int(pid) for pid in run("pgrep", "-x", EMULATOR_PROCESS).split()]


def emulator_gb():
    """Memory the emulator holds in RAM, in GB, or None if it isn't running."""
    sizes = [_rss_gb(pid) for pid in emulator_pids()]
    return max(sizes) if sizes else None


def _rss_gb(pid):
    """Resident memory of process `pid` (VmRSS), in GB; 0 once it is gone."""
    try:
        status = Path(f"/proc/{pid}/status").read_text()
    except FileNotFoundError:
        return 0.0
    kb = re.search(r"^VmRSS:\s+(\d+) kB", status, re.M)
    return int(kb[1]) / 2**20 if kb else 0.0


def _available_gb():
    kb = re.search(r"^MemAvailable:\s+(\d+) kB", Path("/proc/meminfo").read_text(), re.M)
    return int(kb[1]) / 2**20


# --- restarting the device --------------------------------------------------


def on_waydroid():
    """Whether restart() restarts Waydroid rather than the emulator: while its
    session runs (connect() uses it then), or when the emulator isn't running
    either, so a cold start boots Waydroid."""
    return bool(waydroid_ip()) or not emulator_pids()


AVD = "Gaming"       # the Android Studio virtual device the bot runs on
CLOSE_TIMEOUT = 30   # seconds for the emulator to be gone after `emu kill`, before it is killed
BOOT_TIMEOUT = 180   # seconds from opening the emulator to Android having booted
# Cold boot: a quick-boot snapshot would bring back the apps and memory of
# whenever it was saved, and a restart is for a fresh Android.
EMULATOR_ARGS = ["-avd", AVD, "-no-snapshot"]
# A game can come up after a restart laid out for another screen size, where
# nothing matches, and a further restart sets it right (e7/notes/UI.md,
# start-screen, Wrong layout). So a lobby missed after a restart is retried
# with another restart, this many in all.
RESTART_TRIES = 3


def restart(boot_timeout=BOOT_TIMEOUT):
    """(ok, message): close the running apps, close the device (on_waydroid
    picks which), start it again (or just start it if it wasn't running),
    and wait until Android has booted and adb answers. Games are not started."""
    if on_waydroid():
        return _restart_waydroid(boot_timeout)
    emulator = _emulator_exe()
    if emulator_pids():
        _close_apps_before_restart()
    if not _close_emulator():
        return False, "Emulator still open after closing it"
    connect.cache_clear()  # the cached serial belongs to the closed emulator
    # In its own session, so the emulator outlives this process.
    subprocess.Popen([emulator, *EMULATOR_ARGS], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)
    log.info("closed, opening")
    if not wait_until(_booted, boot_timeout, interval=2):
        return False, f"Emulator not booted {boot_timeout}s after opening it"
    return True, "Emulator restarted"


WAYDROID_STOP_TIMEOUT = 30  # seconds for `waydroid session stop` to end the session


def _restart_waydroid(boot_timeout):
    """restart() for Waydroid: stop its session and open its full UI, which
    starts a new session (its window is where the game shows)."""
    if waydroid_ip():
        _close_apps_before_restart()
        try:
            run("waydroid", "session", "stop", timeout=WAYDROID_STOP_TIMEOUT)
        except AdbTimeout as e:
            log.warning(f"{e}")
        if not wait_until(lambda: not waydroid_ip(), 10, interval=0.5):
            return False, "Waydroid session still running after stopping it"
    connect.cache_clear()  # the cached serial belongs to the stopped session
    subprocess.Popen(["waydroid", "show-full-ui"], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)
    log.info("Waydroid stopped, starting it")
    if not wait_until(_booted, boot_timeout, interval=2):
        return False, f"Waydroid not booted {boot_timeout}s after starting it"
    return True, "Waydroid restarted"


def with_room(game, routine):
    """Run routine() with the device's memory kept in check, and return its
    result (False when a restart failed).

    Before it: when the emulator is over EMULATOR_MAX_GB, restart it and bring
    `game` back to its lobby (on Waydroid there is no emulator to measure).
    During it: if it stops on blank screenshots (core.input.BlankScreen) or on
    ADB not answering (core.adb.AdbTimeout), restart the device (restart())
    the same way and run it once more. A rerun is safe because routines start
    by going to their menu from wherever the game is and read what is left
    to do from the screen. The check runs before each routine, since a cold
    start or a long routine can take the emulator past the limit.
    """
    used = None if waydroid_ip() else emulator_gb()
    if used is not None and used > EMULATOR_MAX_GB:
        log.info(f"the emulator uses {used:.1f} GB (over {EMULATOR_MAX_GB}), restarting it first")
        if not _restart_with(game):
            return False
    try:
        return routine()
    except (BlankScreen, AdbTimeout) as e:
        log.warning(f"{e}: restarting the device and running it again")
    if not _restart_with(game):
        return False
    return routine()


def _restart_with(game, tries=RESTART_TRIES):
    """Restart the device, start `game` and take it to its lobby, restarting
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
    """Run the game's lobby routine (its <game>.routines ROUTINES entry),
    which gets past the start screen and its popups too (core.lobby), and
    return its result, or None when the game has none. `game` is a short
    name from GAMES; a package name has no routines here. From the lobby,
    lobby returns at once."""
    if game not in GAMES:
        return None
    module = f"{game}.routines"
    try:
        routines = importlib.import_module(module).ROUTINES
    except ModuleNotFoundError as e:
        if e.name not in (game, module):  # the routines exist but import something missing
            raise
        return None
    if "lobby" not in routines:
        return None
    result = routines["lobby"]()
    log.info(f"{game} lobby: {'ok' if result else 'not done'}")
    return result


def _close_apps_before_restart():
    """Close the apps, logging what happened. Never stops the restart: an
    emulator that needs restarting may not answer adb."""
    try:
        ok, apps = close_apps()
    except RuntimeError as e:  # includes AdbTimeout
        log.warning(f"apps not closed: {e}, closing the emulator anyway")
        return
    if not ok:
        log.warning(f"not all of {', '.join(apps)} stopped, closing the emulator anyway")
    elif apps:
        log.info(f"closed {', '.join(apps)}")


def _emulator_exe():
    path = sdk() / "emulator" / "emulator"
    if not path.exists():
        raise RuntimeError(f"{path} not found. Is the Android emulator installed?")
    return str(path)


def _close_emulator(timeout=CLOSE_TIMEOUT):
    """Close the emulator. Returns True once its process is gone.

    Asks first (`adb emu kill`, which lets it shut down cleanly), and kills
    the process only if it is still there `timeout` seconds later or adb
    can't reach it."""
    if not emulator_pids():
        return True
    try:
        adb("emu", "kill")
    except RuntimeError as e:  # includes AdbTimeout
        log.warning(f"emu kill failed: {e}")
    if wait_until(lambda: not emulator_pids(), timeout, interval=0.5):
        return True
    log.warning(f"the emulator still open {timeout}s after emu kill, killing it")
    for pid in emulator_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return bool(wait_until(lambda: not emulator_pids(), 10, interval=0.5))


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
    elif cmd == "health":
        ok, msg = health()
        _answer(msg, ok)
        sys.exit(0 if ok else 1)
    elif cmd == "restart":
        before = emulator_gb()
        for attempt in range(1, RESTART_TRIES + 1):
            ok, msg = restart()
            now = emulator_gb()
            if ok and now is not None:
                was = f"{before:.1f} GB before" if before is not None else "wasn't running"
                msg += f": {was}, {now:.1f} GB now"
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
            before = emulator_gb()
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
