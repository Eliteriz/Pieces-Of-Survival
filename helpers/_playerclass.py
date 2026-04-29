import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from helpers import game_config as cfg
from helpers import game_utils as utils

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
        if len(self.logs) > cfg.LOG_LIMIT:
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
            "last_played": utils.now_ts(),
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
            info = cfg.ITEMS.get(item, {})
            if "durability" in info:
                while len(p.tool_health.setdefault(item, [])) < qty:
                    p.tool_health[item].append(info["durability"])
        
        return p

    def save(self) -> None:
        path = utils.get_save_path(self.name)
        utils.save_json(path, self.to_dict())

    def add_item(self, item: str, amount: int = 1) -> None:
        self.inventory[item] = self.inventory.get(item, 0) + amount
        info = cfg.ITEMS.get(item, {})
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
            info = cfg.ITEMS.get(item_name, {})
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
        
            self.log(f"{cfg.RED}Your {item_name} broke!{cfg.RESET}")
        
        return True

    def category_of(self, item: str) -> str:
        return cfg.ITEMS.get(item, {}).get("category", "Miscellaneous")

    def tool_matches(self, tool_type: str, tier: int) -> bool:
        for item, amt in self.inventory.items():
            if amt <= 0:
                continue
            info = cfg.ITEMS.get(item, {})
            if info.get("tool_type") == tool_type and info.get("tier", 0) >= tier:
                return True
        return False

    def station_here(self, station: str) -> bool:
        return station in self.world.get(self.location, {}).get("stations", [])

    def ensure_location(self) -> None:
        self.world.setdefault(self.location, {"stations": []})

    def can_craft(self, recipe_name: str) -> Tuple[bool, str]:
        rec = cfg.RECIPES.get(recipe_name)
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
            
            info = cfg.ITEMS.get(item, {})
            if info.get("category") == "Tools" and "durability" in info and dur_cost > 0:
                health_bars = self.tool_health.get(item, [])
                if len(health_bars) < qty:
                    return False, f"Your {item} is missing health data!"
        return True, ""

    def craft(self, recipe_name: str) -> str:
        can, msg = self.can_craft(recipe_name)
        if not can:
            return msg
    
        rec = cfg.RECIPES[recipe_name]
        durability_cost = rec.get("durability_cost", 0)
    
        for item, qty in rec.get("inputs", {}).items():
            info = cfg.ITEMS.get(item, {})

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
                        self.log(f"{cfg.RED}{broken}x {item} broke!{cfg.RESET}")
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
        for recipe_name, rec in cfg.RECIPES.items():
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
        if cfg.ITEMS.get(station, {}).get("category") != "Stations":
            return "Not a station."
        
        self.ensure_location()
        if station in self.world[self.location]["stations"]:
            return "Already placed here."
        
        self.world[self.location]["stations"].append(station)
        self.remove_item(station, 1)
        return f"Placed {station} at {self.location}."

    def seen_bestiary(self, key: str) -> str:
        return key if self.bestiary_seen.get(key) else "???"