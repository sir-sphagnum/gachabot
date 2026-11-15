"""Reverse: 1999 settings shared by the bot and its routines."""

from core import templates_dir
from core.device import package

GAME = "re1999"              # key in core.device.GAMES and this package's name
PACKAGE = package(GAME)      # Android package name
TEMPLATES_DIR = templates_dir(GAME)  # re1999/templates/

# Android Back closes the current menu (Mail back to the lobby), and in the
# lobby opens the "Quit the Game?" dialog.
BACK_KEY = "back"
