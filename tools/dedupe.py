"""Move near-duplicate screenshots out of a folder.

Usage:
    python -m tools.dedupe [folder] [threshold]    # default: recon 1  (percent of pixels changed)
    python -m tools.dedupe recon 1 --dry-run       # print scores, move nothing

Goes through screenshots in the order they were taken and compares each one
to the last one kept. If it barely differs, it is moved to <folder>/dupes/.
click-*.png screenshots are always kept.
"""

import os
import shutil
import sys

import cv2

from core.vision import difference, fingerprint


def dedupe(folder="recon", threshold=1.0, dry_run=False):
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".png")]
    files.sort(key=os.path.getmtime)  # time order, so click-* files land in place
    dupes = os.path.join(folder, "dupes")

    last_kept = None
    kept = moved = 0
    for path in files:
        current = fingerprint(cv2.imread(path, cv2.IMREAD_GRAYSCALE))
        diff = 100.0 if last_kept is None else difference(current, last_kept)
        is_click = os.path.basename(path).startswith("click-")

        if is_click or diff > threshold:
            last_kept = current
            kept += 1
            verdict = "keep"
        else:
            moved += 1
            verdict = "dupe"
            if not dry_run:
                os.makedirs(dupes, exist_ok=True)
                shutil.move(path, dupes)
        print(f"{diff:6.2f}  {verdict}  {os.path.basename(path)}")

    print(f"\nKept {kept}, {'would move' if dry_run else 'moved'} {moved} to {dupes}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    folder = args[0] if len(args) > 0 else "recon"
    threshold = float(args[1]) if len(args) > 1 else 1.0
    dedupe(folder, threshold, dry_run="--dry-run" in sys.argv)
