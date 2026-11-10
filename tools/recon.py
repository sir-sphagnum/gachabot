"""Save a BlueStacks screenshot to recon/ every second, skipping ones that look
the same as the last one saved.

Usage: python -m tools.recon [folder] (Ctrl+C to stop)
"""

import os
import sys
import time
from datetime import datetime

import cv2
import numpy as np

from core.input import capture
from core.vision import difference, fingerprint

THRESHOLD = 1.0  # save only if more than this percent of pixels changed (see core/vision.py)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "recon"
    os.makedirs(folder, exist_ok=True)

    last_saved = None
    while True:
        start = time.time()
        png = capture()
        gray = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE)
        current = fingerprint(gray)

        if last_saved is None or difference(current, last_saved) > THRESHOLD:
            path = os.path.join(folder, datetime.now().strftime("%Y%m%d-%H%M%S") + ".png")
            with open(path, "wb") as f:
                f.write(png)
            last_saved = current
            print(f"Saved {path}", flush=True)

        time.sleep(max(0, 1 - (time.time() - start)))
