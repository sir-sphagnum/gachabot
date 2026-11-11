"""Connect to a running BlueStacks instance over ADB. Usage: python -m core.adb"""

import glob
import subprocess
from functools import cache


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def find_adb():
    """BlueStacks ships its own adb; use that one."""
    paths = glob.glob(r"C:\Program Files\BlueStacks*\HD-Adb.exe")
    if not paths:
        raise RuntimeError("HD-Adb.exe not found. Is BlueStacks installed?")
    return paths[0]


def find_ports():
    """Ports that BlueStacks (HD-Player.exe) is listening on."""
    tasks = run("tasklist", "/FI", "IMAGENAME eq HD-Player.exe", "/FO", "CSV", "/NH")
    pids = {line.split('","')[1] for line in tasks.splitlines() if "HD-Player" in line}

    ports = []
    for line in run("netstat", "-ano", "-p", "TCP").splitlines():
        cols = line.split()  # Proto, Local Address, Foreign Address, State, PID
        if len(cols) == 5 and cols[3] == "LISTENING" and cols[4] in pids:
            ports.append(cols[1].split(":")[-1])
    return ports


@cache
def connect():
    """Return (adb_path, serial) for the first BlueStacks port that accepts ADB."""
    adb = find_adb()
    for port in find_ports():
        serial = f"127.0.0.1:{port}"
        run(adb, "connect", serial)
        if run(adb, "-s", serial, "get-state") == "device":
            return adb, serial
    raise RuntimeError("Could not connect to BlueStacks over ADB. Is it running with ADB enabled?")


def adb(*args):
    """Run an adb command on BlueStacks, e.g. adb("shell", "input", "tap", "400", "400")."""
    adb_path, serial = connect()
    return run(adb_path, "-s", serial, *args)


if __name__ == "__main__":
    adb, serial = connect()
    print(f"Connected to {serial}")
