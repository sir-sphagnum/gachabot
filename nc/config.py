"""Neural Cloud settings shared by the bot and its routines."""

from core import templates_dir
from core.device import package

GAME = "nc"                  # key in core.device.GAMES and this package's name
PACKAGE = package(GAME)      # Android package name
TEMPLATES_DIR = templates_dir(GAME)  # nc/templates/

# The key that closes the current menu: Android Back closes menus (mail
# tested) and opens the quit dialog on the lobby.
BACK_KEY = "back"
