"""Save a BlueStacks screenshot to recon/ every second, skipping ones that look
the same as the last one saved.

Usage: python -m tools.recon [folder] [--interval S]   (Ctrl+C to stop)
       python -m tools.recon --summary [folder]

--interval: seconds between captures (default 1). Every capture adds to
BlueStacks' load: with a routine capturing too, its memory grew fast (see
core.device.health), so slow it down for long runs.
--summary: print how many screenshots the folder holds and their size.

A capture that fails (BlueStacks returning only empty frames, adb not
answering) doesn't end the recording: it's logged and retried after a pause
that doubles up to MAX_BACKOFF seconds, until a capture works again.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from core.input import capture
from core.log import logger, setup
from core.vision import difference, fingerprint, save

log = logger(__file__)

THRESHOLD = 1.0  # save only if more than this percent of pixels changed (see core/vision.py)
MAX_BACKOFF = 30  # seconds between retries while captures keep failing


def summary(folder):
    files = list(Path(folder).glob("*.png"))
    size = sum(f.stat().st_size for f in files) / 2**20
    print(f"{len(files)} screenshots in {folder}/, {size:.0f} MB")


def record(folder, interval):
    os.makedirs(folder, exist_ok=True)
    log.info(f"recording to {folder}/ every {interval:g}s")
    last_saved = None
    backoff = 0
    while True:
        start = time.time()
        try:
            img = capture()
        except RuntimeError as e:  # empty frames, AdbTimeout
            backoff = min(MAX_BACKOFF, backoff * 2 or interval)
            log.warning(f"capture failed ({e}), retrying in {backoff:g}s")
            print(f"Capture failed: {e}", flush=True)
            time.sleep(backoff)
            continue
        if backoff:
            log.info("capturing again")
            backoff = 0
        current = fingerprint(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

        if last_saved is None or difference(current, last_saved) > THRESHOLD:
            path = f"{folder}/{datetime.now():%Y%m%d-%H%M%S}.png"
            save(img, path)
            last_saved = current
            log.debug(f"saved {path}")
            print(f"Saved {path}", flush=True)

        time.sleep(max(0, interval - (time.time() - start)))


if __name__ == "__main__":
    args = sys.argv[1:]
    interval = 1.0
    if "--interval" in args:
        i = args.index("--interval")
        interval = float(args[i + 1])
        del args[i:i + 2]
    if "--summary" in args:
        args.remove("--summary")
        summary(args[0] if args else "recon")
    else:
        setup(console=False)
        record(args[0] if args else "recon", interval)
