import os
import time
import random
from pyfiglet import figlet_format

from helpers import game_config as config
from helpers import game_utils as utils
from helpers import _playerclass as player

def draw_main_ui(p: player.Player) -> None:
    utils.clear_screen()
    print(f"{config.CYAN}{p.name.upper()}{config.RESET} | {config.YELLOW}{p.location}{config.RESET} | {config.RED}HP:{p.health}{config.RESET} | {config.BLUE}MP:{p.mana}{config.RESET} | {config.GREEN}Hunger: {p.hunger}%{config.RESET} |")
    
    stations = p.world.get(p.location, {}).get("stations", [])
    if stations:
        print(f"Stations here: {', '.join(stations)}")
    
    print("\nLogs:")
    for line in p.logs:
        print(f"- {line}")
    print("—" * 20)
    print("[1] Inventory\n[2] Gather\n[3] Travel\n[4] Eat\n[5] Craft\n[6] Research\n[7] Place Station\n[8] Exit")

def show_inventory(p: player.Player) -> None:
    utils.clear_screen()
    print(f"{config.PURPLE}» Inventory «{config.RESET}")
    if not p.inventory:
        print(f"{config.RED}Your inventory is empty!{config.RESET}")
    else:
        categories = ["Materials", "Tools", "Armour", "Ores", "Food", "Preserved Food", "Stations", "Miscellaneous"]
        for cat in categories:
            items = [(i, q) for i, q in p.inventory.items() if p.category_of(i) == cat]
            if items:
                print(f"\n{config.YELLOW}[ {cat} ]:{config.RESET}")
                for item, qty in sorted(items):
                    info = config.ITEMS.get(item, {})
                    if "durability" in info and item in p.tool_health:
                        max_d = info["durability"]
                        health_bars = ", ".join([f"{hp}/{max_d}" for hp in p.tool_health[item]])
                        print(f"{config.YELLOW}- {item} x{qty} {config.CYAN}({health_bars}){config.RESET}")
                    else:
                        print(f"{config.YELLOW}- {item} x{qty}{config.RESET}")
    input("\nEnter to back")

def gather(p: player.Player) -> None:
    place = config.PLACES.get(p.location)
    if not place:
        p.log("Nothing to gather here.")
        return

    drops = place.get("drops", [])
    if not drops:
        p.log("Nothing to gather here.")
        return
    req = place.get("required_tooltier") 
    if req:
        tool_type, min_tier = req
        if not p.tool_matches(tool_type, min_tier):
            p.log(f"Need a tier {min_tier}+ {tool_type}.")
            return
        
        cost = place.get("cost_tick", 1)
        p.wear_tool(tool_type, cost)

    got = random.choices(drops, weights=place.get("w_drop", [1] * len(drops)), k=1)[0]
    amount = random.randint(1, 2)
    p.add_item(got, amount)
    p.log(f"Found {amount}x {got}")

def travel(p: player.Player, audio_manager) -> None:
    utils.clear_screen()
    locs = list(config.PLACES.keys())
    print("Travel")
    for i, loc in enumerate(locs, 1):
        print(f"{i}. {loc}")
    
    choice = utils.input_int("Go where? >> ", valid=range(1, len(locs) + 1), allow_blank=True)
    if choice is None:
        return
    
    p.location = locs[choice - 1]
    p.ensure_location()
    
    track = config.PLACES.get(p.location, {}).get("bgm")
    if track:
        audio_manager.play_bgm(track)
    p.log(f"Moved to {p.location}")

def craft_menu(p: player.Player) -> None:
    while True:
        utils.clear_screen()
        available = [r for r in config.RECIPES if p.researched.get(r, False) or r in p.known_recipes]
        print(f"{config.PURPLE}» Crafting Menu «{config.RESET}")
        
        if not available:
            print("No recipes unlocked yet.")
            input("Enter to back")
            return
            
        for i, recipe in enumerate(available, 1):
            can, msg = p.can_craft(recipe)
            status = f"{config.GREEN}✓{config.RESET}" if can else f"{config.RED}✗ ({msg}){config.RESET}"
            print(f"{i}. {recipe} {status}")
            
        print("0. Back")
        choice = input("Craft which? >> ").strip()
        
        if choice == "0" or choice == "":
            return
            
        try:
            idx = int(choice) - 1
            recipe = available[idx]
        except:
            continue
            
        utils.clear_screen()
        rec = config.RECIPES[recipe]
        dur_cost = rec.get("durability_cost", 0)
        
        print(f"{config.CYAN}Recipe Details: {recipe}{config.RESET}")
        if dur_cost > 0:
            print(f"{config.RED}⚠ Tool Impact: -{dur_cost} Durability per craft{config.RESET}")

        print("\nMaterials needed:")
        max_amt = 999

        for item, qty in rec.get("inputs", {}).items():
            owned = p.inventory.get(item, 0)
            info = config.ITEMS.get(item, {})
            color = config.GREEN if owned >= qty else config.RED
            print(f"- {item}: {color}{owned}/{qty}{config.RESET}")

            if qty > 0:
                max_amt = min(max_amt, owned // qty)

        can, msg = p.can_craft(recipe)
        if not can:
            print(f"{config.RED}{msg}{config.RESET}")
            input("\nEnter to back")
            continue
            
        amt = utils.input_int(f"How many? (0-{max_amt}) >> ", valid=range(0, max_amt + 1), allow_blank=True)
        if not amt:
            continue
            
        crafted = 0
        for _ in range(amt):
            res = p.craft(recipe)
            if "Successfully" in res:
                crafted += 1
            else:
                print(f"{config.RED}{res}{config.RESET}")
                break
                
        if crafted:
            p.log(f"Finished crafting {crafted}x {recipe}")
        time.sleep(0.6)

def research_menu(p: player.Player) -> None:
    utils.clear_screen()
    items = [i for i in p.inventory.keys() if not p.researched.get(i, False)]
    print("Research")
    if not items:
        print("No new items to research.")
        input("Enter to back")
        return

    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    print("0. Back")

    choice = utils.input_int("Research which? >> ", valid=range(0, len(items) + 1), allow_blank=True)
    if not choice:
        return
    item = items[choice - 1]
    p.log(p.research_item(item))

def place_station_menu(p: player.Player) -> None:
    utils.clear_screen()
    stations = [i for i, q in p.inventory.items() if q > 0 and config.ITEMS.get(i, {}).get("category") == "Stations"]
    print("Place Station")
    if not stations:
        print("No stations in inventory.")
        input("Enter to back")
        return

    for i, station in enumerate(stations, 1):
        print(f"{i}. {station}")
    print("0. Back")

    choice = utils.input_int("Place which? >> ", valid=range(0, len(stations) + 1), allow_blank=True)
    if not choice:
        return
    p.log(p.place_station(stations[choice - 1]))

def eat_menu(p: player.Player) -> None:
    utils.clear_screen()
    food_items = [i for i in p.inventory.keys() if p.category_of(i) == "Food"]
    if not food_items:
        print("You have no food!")
        input("\nEnter to back")
        return

    print("What do you want to eat?")
    for i, item in enumerate(food_items, 1):
        info = config.ITEMS.get(item, {})
        restore = info.get("hunger", 0)
        health = info.get("health_restore", 0)
        print(f"{i}. {item} ({config.GREEN}+{restore} Hunger, +{health} Health{config.RESET})")
    
    print("0. Back")
    choice = utils.input_int(">> ", valid=range(0, len(food_items) + 1), allow_blank=True)
    if not choice: return
    
    item_name = food_items[choice - 1]
    info = config.ITEMS.get(item_name, {})
    p.hunger = min(100, p.hunger + info.get("hunger", 0))
    p.health = min(100, p.health + info.get("health_restore", 0))
    p.remove_item(item_name, 1)
    p.log(f"Ate {item_name}. Hunger is now {p.hunger}%.")

def hunger_tick(p: player.Player) -> None:
    p.hunger -= 1
    if p.hunger <= 0:
        p.hunger = 0
        p.health -= 5
        p.log(f"{config.RED}You're starving and losing health!{config.RESET}")

def start_screen(audio_manager, load_addons_func, list_saves_func) -> player.Player:
    audio_manager.play_bgm("main_menu.mp3")
    utils.clear_screen()
    
    if not os.path.exists("mods"):
        os.makedirs("mods")
    
    mods = [f for f in os.listdir("mods") if f.endswith(".mpos")]
    selected_indices = [0]    
    while True:
        utils.clear_screen()
        print(f"{config.GREEN}{figlet_format('Pieces of Survival')}{config.RESET}")
        print(f"{config.CYAN}--- MOD / ADDON SELECTOR ---{config.RESET}")
        print("Select your packs (Type 'done' to start game):")

        v_status = "X" if 0 in selected_indices else " "
        print(f"0. [{v_status}] Vanilla (Core Game)")
        
        for i, m in enumerate(mods, 1):
            status = "X" if i in selected_indices else " "
            print(f"{i}. [{status}] {m.replace('.mpos', '')}")
            
        choice = input("\nToggle number or type 'done' >> ").lower().strip()
        
        if choice == 'done':
            if not selected_indices:
                selected_indices = [0]
            break
            
        try:
            idx = int(choice)
            if 0 <= idx <= len(mods):
                if idx in selected_indices: selected_indices.remove(idx)
                else: selected_indices.append(idx)
        except ValueError:
            print(f"{config.RED}Please enter a number or 'done'.{config.RESET}")
            time.sleep(0.5)

    selected_indices.sort()
    paths_to_load = []
    mod_names = []
    
    for idx in selected_indices:
        if idx == 0:
            paths_to_load.append(config.IDATA_PATH)
            mod_names.append("vanilla")
        else:
            filename = mods[idx-1]
            paths_to_load.append(os.path.join("mods", filename))
            mod_names.append(filename.replace(".mpos", ""))

    current_mod_combined = "_".join(mod_names)
    load_addons_func(paths_to_load)
    
    saves = list_saves_func(current_mod_combined) 
    utils.clear_screen()
    print(f"{config.PURPLE}--- {current_mod_combined.upper()} SAVES ---{config.RESET}")
    if not saves:
        print("No saves found.")
    else:
        for i, (name, _) in enumerate(saves, 1):
            print(f"{i}. {name}")
    
    print(f"{len(saves) + 1}. Create New Character")
    save_choice = input("\nChoose save >> ").strip()
    
    if save_choice.isdigit() and 1 <= int(save_choice) <= len(saves):
        char_name = saves[int(save_choice) - 1][0]
        data = utils.load_json(os.path.join(config.DATA_DIR, f"players_{current_mod_combined}", f"{char_name}.json"), {})
        return player.Player.from_dict(char_name, data)

    name = input("Enter Character Name: ").strip() or "Player"
    start_loc = list(config.PLACES.keys())[0] if config.PLACES else "Forest"
    p = player.Player(name=name, location=start_loc)
    p.save() 
    return p