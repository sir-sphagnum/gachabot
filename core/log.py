"""Logging for routines and navigation. Rules: .claude/logging.md.

Modules take their logger with `log = logger(__file__)`; command-line entry
points call setup() once, with debug=True for --debug.
"""

import logging
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def logger(file):
    """The logger for the module in `file`, named after it (e.g. "lobby").

    Named from the file, not __name__: under `python -m e7.routines.lobby`,
    __name__ is "__main__"."""
    return logging.getLogger(Path(file).stem)


def setup(debug=False):
    """Print log lines in FORMAT: INFO and above, or everything with debug."""
    logging.basicConfig(format=FORMAT, datefmt="%H:%M:%S",
                        level=logging.DEBUG if debug else logging.INFO)
