"""Arknights settings shared by the bot and its routines."""

from core import templates_dir
from core.device import package

GAME = "ak"                  # key in core.device.GAMES and this package's name
PACKAGE = package(GAME)      # Android package name
TEMPLATES_DIR = templates_dir(GAME)  # ak/templates/

# The key that closes the current menu: Android Back.
BACK_KEY = "back"
