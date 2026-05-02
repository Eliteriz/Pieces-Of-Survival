import os

CURRENT_MOD_NAME = "vanilla"

DATA_DIR = "data"
IDATA_PATH = os.path.join("idata.json")
EDATA_PATH = os.path.join("edata.json")

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
PURPLE = "\033[95m"

LOG_LIMIT = 5

ITEMS = {}
RECIPES = {}
PLACES = {}
BESTIARY = {}
ENEMIES = {}
ENEMY_SKILLS = {}
WEAPON_SKILLS = {}
EQUIPPED_WEAPON = None
