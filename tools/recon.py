"""Save a BlueStacks screenshot to recon/ every second, skipping ones that look
the same as the last one saved.

Usage: python -m tools.recon [folder] (Ctrl+C to stop)
"""

import os
import sys
import time
from datetime import datetime

import cv2

from core.input import capture
from core.log import logger, setup
from core.vision import difference, fingerprint, save

log = logger(__file__)

THRESHOLD = 1.0  # save only if more than this percent of pixels changed (see core/vision.py)


if __name__ == "__main__":
    setup(console=False)
    folder = sys.argv[1] if len(sys.argv) > 1 else "recon"
    os.makedirs(folder, exist_ok=True)
    log.info(f"recording to {folder}/")

    last_saved = None
    while True:
        start = time.time()
        img = capture()
        current = fingerprint(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

        if last_saved is None or difference(current, last_saved) > THRESHOLD:
            path = f"{folder}/{datetime.now():%Y%m%d-%H%M%S}.png"
            save(img, path)
            last_saved = current
            log.debug(f"saved {path}")
            print(f"Saved {path}", flush=True)

        time.sleep(max(0, 1 - (time.time() - start)))
