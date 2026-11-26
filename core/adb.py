"""Connect over ADB to the Android the bot runs on: Waydroid while its session
runs, else the Android Studio emulator. Usage: python -m core.adb"""

import os
import re
import subprocess
from functools import cache
from pathlib import Path

# Seconds any one command may take. Without a limit, a call that never returns
# (an emulator out of memory) freezes a whole run with no log line.
TIMEOUT = 20


class AdbTimeout(RuntimeError):
    """A command run here gave no answer within its timeout."""


def run(*cmd, timeout=TIMEOUT):
    return run_bytes(*cmd, timeout=timeout).decode(errors="replace").strip()


def run_bytes(*cmd, timeout=TIMEOUT):
    """Run cmd and return its stdout as bytes. Raises AdbTimeout after `timeout` seconds."""
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        raise AdbTimeout(f"{Path(cmd[0]).name} {' '.join(map(str, cmd[1:]))}: "
                         f"no answer in {timeout}s") from None


def sdk():
    """The Android SDK folder: $ANDROID_HOME, else Android Studio's default."""
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    return Path(home) if home else Path.home() / "Android" / "Sdk"


def find_adb():
    """The SDK's adb, not one on PATH: an adb of another version restarts the
    adb server as its own, dropping the connections of the one running."""
    path = sdk() / "platform-tools" / "adb"
    if not path.exists():
        raise RuntimeError(f"{path} not found. Is the Android SDK installed?")
    return str(path)


WAYDROID_PORT = 5555  # Waydroid's adbd listens on its container IP at this port


def waydroid_ip():
    """The Waydroid container's IP while its session runs, else None (also
    when Waydroid isn't installed)."""
    try:
        status = run("waydroid", "status")
    except FileNotFoundError:
        return None
    if not re.search(r"^Session:\s+RUNNING", status, re.M):
        return None
    ip = re.search(r"^IP address:\s+(\S+)", status, re.M)
    return ip[1] if ip else None


@cache
def connect():
    """Return (adb_path, serial) for the device the bot runs on: Waydroid
    ("192.168.240.112:5555") while its session runs, else the first emulator
    adb lists as ready ("emulator-5554").

    Waydroid has to be connected (`adb connect`), and the first connection
    from this PC waits for "Allow USB debugging" to be accepted in Waydroid.
    The emulator registers itself."""
    adb = find_adb()
    ip = waydroid_ip()
    if ip:
        serial = f"{ip}:{WAYDROID_PORT}"
        run(adb, "connect", serial)
        state = run(adb, "-s", serial, "get-state")
        if state != "device":
            raise RuntimeError(f"Waydroid at {serial} is {state or 'not answering'} over ADB"
                               " (unauthorized: accept Allow USB debugging in Waydroid)")
        return adb, serial
    for line in run(adb, "devices").splitlines()[1:]:
        serial, _, state = line.partition("\t")
        if serial.startswith("emulator-") and state == "device":
            return adb, serial
    raise RuntimeError("No Waydroid session or emulator ready over ADB."
                       " Start one with: python -m core.device restart")


def adb(*args):
    """Run an adb command on the device, e.g. adb("shell", "input", "tap", "400", "400")."""
    adb_path, serial = connect()
    return run(adb_path, "-s", serial, *args)


if __name__ == "__main__":
    adb, serial = connect()
    print(f"Connected to {serial}")
