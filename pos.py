import os
import sys
import time
import random
from typing import List, Tuple

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Modules
from helpers import game_config as config
from helpers import game_utils as utils
from helpers import _playerclass as player
from helpers import ui
from sound_manager import SoundManager

audio = SoundManager()

def load_addons(paths: List[str]):
    # syncs mod data into the global config registries.
    config.ITEMS.clear()
    config.RECIPES.clear()
    config.PLACES.clear()
    config.BESTIARY.clear()

    for r in range(3):
        utils.clear_screen()
        time.sleep(0.1)
        print(f"{config.CYAN}Synchronizing...{config.RESET}")
        time.sleep(0.15)
    print("—" * 30)

    for path in paths:
        data = utils.load_json(path, {})
        mod_label = os.path.basename(path).replace(".mpos", "")
        
        for item_id, item_info in data.get("items", {}).items():
            if item_id in config.ITEMS:
                print(f"⚠️  [Conflict] '{item_id}' exists. Skipping {mod_label} {config.RED}[BAD]{config.RESET}")
            else:
                config.ITEMS[item_id] = item_info
                print(f"[ITEMS] Appended: {item_id:.<15} {config.GREEN}[OK]{config.RESET}")
                time.sleep(random.uniform(0.01, 0.04))

        for rec_id, rec_info in data.get("recipes", {}).items():
            if rec_id in config.RECIPES:
                print(f"⚠️  [Conflict] Recipe '{rec_id}' exists. Skipping {mod_label} {config.RED}[BAD]{config.RESET}")
            else:
                config.RECIPES[rec_id] = rec_info
                print(f"[RECIPES] Appended: {rec_id:.<15} {config.GREEN}[OK]{config.RESET}")
                time.sleep(random.uniform(0.01, 0.04))
         
        for place_id, place_info in data.get("places", {}).items():
            if place_id in config.PLACES:
                print(f"⚠️  [Conflict] Place '{place_id}' exists. Skipping {mod_label} {config.RED}[BAD]{config.RESET}")
            else:
                config.PLACES[place_id] = place_info
                print(f"[PLACES] Appended: {place_id:.<15} {config.GREEN}[OK]{config.RESET}")
                time.sleep(random.uniform(0.01, 0.04))
                
    time.sleep(1)
    print(f"\n{config.GREEN}Successfully synchronized {len(paths)} source(s).{config.RESET}")
    input("Enter to continue... [READY]")

def list_saves(mod_name: str) -> List[Tuple[str, int]]:
    specific_players_dir = os.path.join(config.DATA_DIR, f"players_{mod_name}")
    os.makedirs(specific_players_dir, exist_ok=True)
    saves = []
    for file in os.listdir(specific_players_dir):
        if file.endswith(".json"):
            path = os.path.join(specific_players_dir, file)
            data = utils.load_json(path, {})
            saves.append((file[:-5], data.get("last_played", 0)))
    saves.sort(key=lambda x: x[1], reverse=True)
    return saves

def main() -> None:
    p = ui.start_screen(audio, load_addons, list_saves)
    p.ensure_location()
    
    track = config.PLACES.get(p.location, {}).get("bgm")
    if track:
        audio.play_bgm(track)
    else:
        audio.stop_bgm()
    
    hloop = 0

    while True:
        try:
            ui.draw_main_ui(p)
            print("\nWhat do you want to do?")
            action = input("> ").strip()

            if action == "1":
                ui.show_inventory(p)
            elif action == "2":
                ui.gather(p)
            elif action == "3":
                ui.travel(p, audio)
            elif action == "4":
                ui.eat_menu(p)
            elif action == "5":
                ui.craft_menu(p)
            elif action == "6":
                ui.research_menu(p)
            elif action == "7":
                ui.place_station_menu(p)
            elif action == "8":
                utils.clear_screen()
                print(f"{config.GREEN}Saving Data...{config.RESET}")
                p.save()
                time.sleep(1)
                print(f"Goodbye {p.name}!")
                audio.stop_bgm()
                break
            else:
                p.log("Invalid action.")

            hloop += 1
            if hloop >= 3:
                ui.hunger_tick(p)
                hloop = 0
            
            p.save()
        
        except Exception as e:
            p.log(f"System error: {e}")
            p.save()
            time.sleep(2)

if __name__ == "__main__":
    main()