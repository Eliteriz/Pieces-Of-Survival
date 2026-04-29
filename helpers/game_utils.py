import os
import json
import time
import random
from typing import Optional
from helpers import game_config as cfg

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def now_ts() -> int:
    return int(time.time())

def get_save_path(player_name: str) -> str:
    folder = os.path.join(cfg.DATA_DIR, f"players_{cfg.CURRENT_MOD_NAME}")
    return os.path.join(folder, f"{player_name}.json")

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def input_int(prompt: str, valid: Optional[range] = None, allow_blank: bool = False) -> Optional[int]:
    while True:
        raw = input(prompt).strip()
        if allow_blank and raw == "":
            return None
        try:
            value = int(raw)
            if valid is not None and value not in valid:
                print(f"{cfg.RED}Invalid choice.{cfg.RESET}")
                continue
            return value
        except ValueError:
            print(f"{cfg.RED}Enter a number.{cfg.RESET}")