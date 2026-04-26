import json
import os
import random
import time
from sound_manager import SoundManager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pyfiglet import figlet_format

audio = SoundManager()
CURRENT_MOD_NAME = "vanilla"
DATA_DIR = "data"
PLAYERS_DIR = os.path.join(DATA_DIR, "players")
IDATA_PATH = os.path.join("idata.json")

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
PURPLE = "\033[95m"

LOG_LIMIT = 5

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def get_save_path(player_name: str) -> str:
    folder = os.path.join(DATA_DIR, f"players_{CURRENT_MOD_NAME}")
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

def now_ts() -> int:
    return int(time.time())

idata = load_json(IDATA_PATH, {"items": {}, "recipes": {}, "places": {}, "bestiary": {}})
ITEMS = idata.get("items", {})
RECIPES = idata.get("recipes", {})
PLACES = idata.get("places", {})
BESTIARY = idata.get("bestiary", {})


def fmt(label: str, value: str) -> str:
    return f"{label}{value}{RESET}"

def input_int(prompt: str, valid: Optional[range] = None, allow_blank: bool = False) -> Optional[int]:
    while True:
        raw = input(prompt).strip()
        
        if allow_blank and raw == "":
            return None
        try:
            value = int(raw)
            if valid is not None and value not in valid:
                print(f"{RED}Invalid choice.{RESET}")
                continue
            return value
        except ValueError:
            print(f"{RED}Enter a number.{RESET}")

@dataclass
class Player:
    name: str
    location: str = "Forest"
    health: int = 100
    mana: int = 100
    hunger: int = 100
    inventory: Dict[str, int] = field(default_factory=dict)
    tool_health: Dict[str, List[int]] = field(default_factory=dict)
    known_recipes: List[str] = field(default_factory=list)
    researched: Dict[str, bool] = field(default_factory=dict)
    world: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    bestiary_seen: Dict[str, bool] = field(default_factory=dict)
    logs: List[str] = field(default_factory=lambda: ["Welcome back to the Shire.", "Safe travels, wanderer."])

    def log(self, message: str) -> None:
        self.logs.append(message)
        if len(self.logs) > LOG_LIMIT:
            self.logs.pop(0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "health": self.health,
            "mana": self.mana,
            "hunger": self.hunger,
            "inventory": self.inventory,
            "tool_health": self.tool_health,
            "known_recipes": self.known_recipes,
            "researched": self.researched,
            "world": self.world,
            "bestiary_seen": self.bestiary_seen,
            "last_played": now_ts(),
        }

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "Player":
        p = cls(name=name)
        p.location = data.get("location", "Forest")
        p.health = data.get("health", 100)
        p.mana = data.get("mana", 100)
        p.hunger = data.get("hunger", 100)
        p.inventory = data.get("inventory", {})
        p.known_recipes = data.get("known_recipes", [])
        p.researched = data.get("researched", {})
        p.world = data.get("world", {})
        p.bestiary_seen = data.get("bestiary_seen", {})
        
        for recipe in p.known_recipes:
            p.researched[recipe] = True
        
        for item, qty in p.inventory.items():
            info = ITEMS.get(item, {})
            if "durability" in info:
                while len(p.tool_health.setdefault(item, [])) < qty:
                    p.tool_health[item].append(info["durability"])
        
        return p

    def save(self) -> None:
        path = get_save_path(self.name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        save_json(path, self.to_dict())

    def add_item(self, item: str, amount: int = 1) -> None:
        self.inventory[item] = self.inventory.get(item, 0) + amount
        info = ITEMS.get(item, {})
        if "durability" in info:
            max_d = info["durability"]
            for _ in range(amount):
                self.tool_health.setdefault(item, []).append(max_d)

    def remove_item(self, item: str, amount: int = 1) -> bool:
        if self.inventory.get(item, 0) < amount:
            return False
        self.inventory[item] -= amount
        if self.inventory[item] <= 0:
            self.inventory.pop(item)
            if item in self.tool_health:
                self.tool_health.pop(item)
        return True

    def wear_tool(self, tool_type: str, amount: int) -> bool:
        if not tool_type:
            return False
        
        candidates = []
        
        for item_name, qty in self.inventory.items():
            info = ITEMS.get(item_name, {})
            if info.get("tool_type") == tool_type and item_name in self.tool_health:
                for i, hp in enumerate(self.tool_health[item_name]):
                    candidates.append((item_name, i, hp))
        
        if not candidates:
            return False
        
        item_name, idx, hp = min(candidates, key=lambda x: x[2])
        self.tool_health[item_name][idx] -= amount
        
        if self.tool_health[item_name][idx] <= 0:
            self.tool_health[item_name].pop(idx)
            self.inventory[item_name] -= 1
        
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]
                self.tool_health.pop(item_name, None)
        
            self.log(f"{RED}Your {item_name} broke!{RESET}")
        
        return True

    def category_of(self, item: str) -> str:
        return ITEMS.get(item, {}).get("category", "Miscellaneous")
    def tool_matches(self, tool_type: str, tier: int) -> bool:
        for item, amt in self.inventory.items():
            if amt <= 0:
                continue
            info = ITEMS.get(item, {})
            if info.get("tool_type") == tool_type and info.get("tier", 0) >= tier:
                return True
        return False

    def station_here(self, station: str) -> bool:
        return station in self.world.get(self.location, {}).get("stations", [])
    def ensure_location(self) -> None:
        self.world.setdefault(self.location, {"stations": []})

    def can_craft(self, recipe_name: str) -> Tuple[bool, str]:
        rec = RECIPES.get(recipe_name)
        if not rec:
            return False, "Unknown recipe."

        req_station = rec.get("station")
        if req_station:
            req_list = req_station if isinstance(req_station, list) else [req_station]
            if not any(self.station_here(s) for s in req_list):
                return False, f"Needs station: {', '.join(req_list)}"

        dur_cost = rec.get("durability_cost", 0)

        for item, qty in rec.get("inputs", {}).items():
            if self.inventory.get(item, 0) < qty:
                return False, f"Missing: {item}"
            
            info = ITEMS.get(item, {})
            if info.get("category") == "Tools" and "durability" in info and dur_cost > 0:
                health_bars = self.tool_health.get(item, [])
                if len(health_bars) < qty:
                    return False, f"Your {item} is missing health data!"
        return True, ""

    def craft(self, recipe_name: str) -> str:
        can, msg = self.can_craft(recipe_name)
        if not can:
            return msg
    
        rec = RECIPES[recipe_name]
        durability_cost = rec.get("durability_cost", 0)
    
        for item, qty in rec.get("inputs", {}).items():
            info = ITEMS.get(item, {})

            if info.get("category") == "Tools" and "durability" in info:
                health_list = self.tool_health.get(item, [])
    
                if durability_cost > 0:
                    if len(health_list) < qty:
                        return f"Failed: Not enough usable {item}"
                    
                    for i in range(qty):
                        health_list[i] -= durability_cost
                    new_health = []
                    broken = 0
                    for hp in health_list:
                        if hp > 0:
                            new_health.append(hp)
                        else:
                            broken += 1
                    self.tool_health[item] = new_health
                    if broken > 0:
                        self.inventory[item] -= broken
                        if self.inventory[item] <= 0:
                            del self.inventory[item]
                            self.tool_health.pop(item, None)
                        self.log(f"{RED}{broken}x {item} broke!{RESET}")
                else:
                    self.remove_item(item, qty)
            else:
                self.remove_item(item, qty)
    
        self.add_item(recipe_name, 1)
        return f"Successfully crafted {recipe_name}!"

    def research_item(self, item: str) -> str:
        if item not in self.inventory:
            return "You do not have that item."
        if self.researched.get(item):
            return f"{item} already researched."
        self.researched[item] = True
        unlocked = []
        for recipe_name, rec in RECIPES.items():
            if recipe_name in self.known_recipes:
                continue
            if all(self.researched.get(i, False) or i in self.known_recipes for i in rec.get("inputs", {})):
                self.known_recipes.append(recipe_name)
                self.researched[recipe_name] = True
                unlocked.append(recipe_name)
        return f"Researched {item}. Unlocked: {', '.join(unlocked) if unlocked else 'None'}"

    def place_station(self, station: str) -> str:
        if self.inventory.get(station, 0) <= 0:
            return "Missing item."
        if ITEMS.get(station, {}).get("category") != "Stations":
            return "Not a station."
        self.ensure_location()
        if station in self.world[self.location]["stations"]:
            return "Already placed here."
        self.world[self.location]["stations"].append(station)
        self.remove_item(station, 1)
        return f"Placed {station} at {self.location}."

    def seen_bestiary(self, key: str) -> str:
        return key if self.bestiary_seen.get(key) else "???"

def list_saves(mod_name: str) -> List[Tuple[str, int]]:
    specific_players_dir = os.path.join(DATA_DIR, f"players_{mod_name}")
    os.makedirs(specific_players_dir, exist_ok=True)
    saves = []
    for file in os.listdir(specific_players_dir):
        if not file.endswith(".json"):
            continue
        
        path = os.path.join(specific_players_dir, file)
        data = load_json(path, {})
        saves.append((file[:-5], data.get("last_played", 0)))
    saves.sort(key=lambda x: x[1], reverse=True)
    return saves

def load_player(name: str) -> Player:
    path = get_save_path(name)
    data = load_json(path, {})
    return Player.from_dict(name, data)

def draw_main_ui(p: Player) -> None:
    clear_screen()
    print(f"{CYAN}{p.name.upper()}{RESET} | {YELLOW}{p.location}{RESET} | {RED}HP:{p.health}{RESET} | {BLUE}MP:{p.mana}{RESET} | {GREEN}Hunger: {p.hunger}%{RESET} |")
    stations = p.world.get(p.location, {}).get("stations", [])
    if stations:
        print(f"Stations here: {', '.join(stations)}")
    print()
    print("Logs:")
    for line in p.logs:
        print(f"- {line}")
    print("—"*20)
    print("[1] Inventory\n[2] Gather\n[3] Travel\n[4] Eat\n[5] Craft\n[6] Research\n[7] Place Station\n[8] Exit")

def show_inventory(p: Player) -> None:
    clear_screen()
    print(f"{PURPLE}» Inventory «{RESET}")
    if not p.inventory:
        print(f"{RED}Your inventory is empty!{RESET}")
    else:
        categories = ["Materials", "Tools", "Armour", "Ores", "Food", "Preserved Food", "Stations", "Miscellaneous"]
        for cat in categories:
            items = [(i, q) for i, q in p.inventory.items() if p.category_of(i) == cat]
            if items:
                print(f"\n{YELLOW}[ {cat} ]:{RESET}")
                for item, qty in sorted(items):
                    info = ITEMS.get(item, {})
                    if "durability" in info and item in p.tool_health:
                        max_d = info["durability"]
                        health_bars = ", ".join([f"{hp}/{max_d}" for hp in p.tool_health[item]])
                        print(f"{YELLOW}- {item} x{qty} {CYAN}({health_bars}){RESET}")
                    else:
                        print(f"{YELLOW}- {item} x{qty}{RESET}")
    input("\nEnter to back")

def gather(p: Player) -> None:
    place = PLACES.get(p.location)
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

def travel(p: Player) -> None:
    clear_screen()
    locs = list(PLACES.keys())
    print("Travel")
    for i, loc in enumerate(locs, 1):
        print(f"{i}. {loc}")
    choice = input_int("Go where? >> ", valid=range(1, len(locs) + 1), allow_blank=True)
    if choice is None:
        return
    p.location = locs[choice - 1]
    p.ensure_location()
    track = PLACES.get(p.location, {}).get("bgm")
    if track:
        audio.play_bgm(track)
    p.log(f"Moved to {p.location}")

def craft_menu(p: Player) -> None:
    while True:
        clear_screen()
        available = [r for r in RECIPES if p.researched.get(r, False) or r in p.known_recipes]
        print(f"{PURPLE}» Crafting Menu «{RESET}")
        
        if not available:
            print("No recipes unlocked yet.")
            input("Enter to back")
            return
            
        for i, recipe in enumerate(available, 1):
            can, msg = p.can_craft(recipe)
            status = f"{GREEN}✓{RESET}" if can else f"{RED}✗ ({msg}){RESET}"
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
            
        clear_screen()
        rec = RECIPES[recipe]
        dur_cost = rec.get("durability_cost", 0)
        
        print(f"{CYAN}Recipe Details: {recipe}{RESET}")
        if dur_cost > 0:
            print(f"{RED}⚠ Tool Impact: -{dur_cost} Durability per craft{RESET}")

        print("\nMaterials needed:")
        max_amt = 999

        for item, qty in rec.get("inputs", {}).items():
            owned = p.inventory.get(item, 0)
            info = ITEMS.get(item, {})
            is_tool = info.get("category") == "Tools"
            has_durability = "durability" in info
            
            color = GREEN if owned >= qty else RED

            if is_tool and has_durability:
                healths = p.tool_health.get(item, [])
                h_str = ", ".join([f"{h}/{info['durability']}" for h in healths])
                print(f"- {item}: {color}{owned}/{qty}{RESET} {YELLOW}(HP: {h_str}){RESET}")
            elif is_tool:
                print(f"- {item}: {color}{owned}/{qty}{RESET} {CYAN}(Consumable Tool){RESET}")
            else:
                print(f"- {item}: {color}{owned}/{qty}{RESET}")

            if qty > 0:
                max_amt = min(max_amt, owned // qty)

            if is_tool and has_durability and dur_cost > 0:
                healths = p.tool_health.get(item, [])
                total_uses = sum(h // dur_cost for h in healths)
                max_amt = min(max_amt, total_uses)

        req_station = rec.get("station")
        if req_station:
            req_list = req_station if isinstance(req_station, list) else [req_station]
            has_station = any(p.station_here(s) for s in req_list)
            status = f"{GREEN}✓{RESET}" if has_station else f"{RED}✗{RESET}"
            print(f"\nStation: {', '.join(req_list)} {status}")
            if not has_station:
                max_amt = 0

        print(f"\n{BLUE}Max possible: {max_amt}{RESET}")
        
        can, msg = p.can_craft(recipe)
        if not can:
            print(f"{RED}{msg}{RESET}")
            input("\nEnter to back")
            continue
            
        amt = input_int(f"How many? (0-{max_amt}) >> ", valid=range(0, max_amt + 1), allow_blank=True)
        if not amt:
            continue
            
        crafted = 0
        for _ in range(amt):
            result = p.craft(recipe)
            if "Successfully" in result:
                crafted += 1
            else:
                print(f"{RED}{result}{RESET}")
                break
                
        if crafted:
            p.log(f"Finished crafting {crafted}x {recipe}")
        time.sleep(0.6)

def research_menu(p: Player) -> None:
    clear_screen()
    items = [i for i in p.inventory.keys() if not p.researched.get(i, False)]
    print("Research")
    if not items:
        print("No new items to research.")
        input("Enter to back")
        
        return

    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    print("0. Back")

    choice = input_int("Research which? >> ", valid=range(0, len(items) + 1), allow_blank=True)
    if not choice:
        return
    item = items[choice - 1]
    p.log(p.research_item(item))

def place_station_menu(p: Player) -> None:
    clear_screen()
    stations = [i for i, q in p.inventory.items() if q > 0 and ITEMS.get(i, {}).get("category") == "Stations"]
    print("Place Station")
    if not stations:
        print("No stations in inventory.")
        input("Enter to back")
        
        return

    for i, station in enumerate(stations, 1):
        print(f"{i}. {station}")
    print("0. Back")

    choice = input_int("Place which? >> ", valid=range(0, len(stations) + 1), allow_blank=True)
    if not choice:
        return
    p.log(p.place_station(stations[choice - 1]))
    
def hunger_tick(p: Player) -> None:
    p.hunger -= 1
    if p.hunger <= 0:
        p.hunger = 0
        p.health -= 5
        p.log(f"{RED}You're starving and losing health. Go get something to eat!{RESET}")

def eat_menu(p: Player) -> None:
    clear_screen()
    food_items = [i for i in p.inventory.keys() if p.category_of(i) == "Food"]
    if not food_items:
        print("You have no food!")
        input("\nEnter to back")
        
        return
    print("What do you want to eat?")
    for i, item in enumerate(food_items, 1):
        restore = ITEMS.get(item, {}).get("hunger", 0)
        print(f"{i}. {item} (+{restore} Hunger)")
    print("0. Back")
    choice = input_int(">> ", valid=range(0, len(food_items) + 1), allow_blank=True)
    if not choice: return
    item_name = food_items[choice - 1]
    hunger_restore = ITEMS.get(item_name, {}).get("hunger", 0)
    health_restore = ITEMS.get(item_name , {}).get("health_restore", 0)
    p.hunger = min(100, p.hunger + hunger_restore)
    p.health = min(100, p.health + health_restore)
    p.remove_item(item_name, 1)
    p.log(f"Ate {item_name}. Hunger is now {p.hunger}%. And Restored {health_restore} health.")

def start_screen() -> Player:
    global CURRENT_MOD_NAME
    audio.play_bgm("main_menu.mp3")
    clear_screen()
    if not os.path.exists("mods"):
        os.makedirs("mods")
    
    mods = [f for f in os.listdir("mods") if f.endswith(".mpos")]
    
    print(f"{GREEN}{figlet_format('Pieces of Survival')}{RESET}")
    print("Select World / Mod:")
    print("0. Vanilla")
    for i, m in enumerate(mods, 1):
        print(f"{i}. {m.replace('.mpos', '')}")
        
    m_choice = input_int(">> ", valid=range(0, len(mods) + 1))
    
    if m_choice == 0:
        CURRENT_MOD_NAME = "vanilla"
    else:
        selected_file = mods[m_choice - 1]
        CURRENT_MOD_NAME = selected_file.replace(".mpos", "")
        load_mod_data(selected_file)

    saves = list_saves(CURRENT_MOD_NAME) 
    clear_screen()
    print(f"{CYAN}--- {CURRENT_MOD_NAME.upper()} SAVES ---{RESET}")
    for i, (name, _) in enumerate(saves, 1):
        print(f"{i}. {name}")
    print(f"{len(saves) + 1}. New Character")

    choice = input("\nChoose save >> ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(saves):
        return load_player(saves[int(choice) - 1][0])

    name = input("Username: ").strip() or "Player"
    p = Player(name=name)
    p.save() 
    return p

def main() -> None:
    hloop = 0
    p = start_screen()
    p.ensure_location()
    track = PLACES.get(p.location, {}).get("bgm")
    if track:
        audio.play_bgm(track)
    else: audio.stop_bgm()
    
    while True:
        try:
            draw_main_ui(p)
            print("\nWhat do you want to do?")
            action = input("> ").strip()

            if action == "1":
                show_inventory(p)
            elif action == "2":
                gather(p)
            elif action == "3":
                travel(p)
            elif action == "4":
                eat_menu(p)
            elif action == "5":
                craft_menu(p)
            elif action == "6":
                research_menu(p)
            elif action == "7":
                place_station_menu(p)
            elif action == "8":
                clear_screen()
                print(f"{GREEN}Saving Data...{RESET}")
                p.save()
                time.sleep(1)
                print(f"Goodbye {p.name}!")
                audio.stop_bgm()
                break
            else:
                p.log("Invalid action.")
            hloop += 1
            p.save()
            if hloop == 3:
                hunger_tick(p)
                hloop = 0
        
        except Exception as e:
            p.log(f"System error: {e}")
            p.save()
            time.sleep(1)

    p.save()

if __name__ == "__main__":
    main()