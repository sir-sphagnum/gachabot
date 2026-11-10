"""E7 settings shared by the bot and its routines."""

from core import templates_dir
from core.device import package

GAME = "e7"                  # key in core.device.GAMES and this package's name
PACKAGE = package(GAME)      # Android package name
TEMPLATES_DIR = templates_dir(GAME)  # e7/templates/

# In E7, Android Back drops to the home screen, while Escape closes the
# current menu like pressing Esc on PC does.
BACK_KEY = "escape"
