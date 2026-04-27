# Pieces of Survival (beta)
- Get materials in various places. Use tools to gather even powerful tool.
- Research the materials you got, and craft them into something useful.

---

## Modding: Contributing via Pull Request

- **Format:** JSON
- **Mod name:** `[MOD_NAME].mpos`

### Addon Structure
Your `.mpos` file should follow this template:

```json
{
  "items": {
    "Iron Ore": {"category": "Materials", "researched": false},
    "Iron Pickaxe": {
      "category": "Tools",
      "tool_type": "pickaxe",
      "tier": 2,
      "durability": 100,
      "researched": false
    },
    "Grilled Fish": {
      "category": "Food",
      "researched": false,
      "hunger": 40,
      "health_restore": 10
    }
  },
  "recipes": {
    "Iron Pickaxe": {
      "inputs": {"Iron Ore": 3, "Branch": 2},
      "station": ["Furnace"],
      "durability_cost": 5
    },
    "Grilled Fish": {
      "inputs": {"Salmon on a stick": 1},
      "station": ["Campfire"]
    }
  },
  "places": {
    "Deep Cave": {
      "drops": ["Iron Ore", "Coal", "Stone"],
      "w_drop": [20, 30, 50],
      "required_tooltier": ["pickaxe", 2],
      "cost_tick": 3
    }
  }
}
```
#### Template Details:
- Items:
•` tool_type` & `tier`: Required for tools to unlock specific places.
• `durability`: Starting health of the tool.
• `hunger` & `health_restore`: Used only for Food category.
- Recipes:
• `inputs: {"ItemName": Quantity}.`
• `station`: A list of required stations ["Station A", "Station B"] or null.
• `durability_cost`: Amount of durability consumed from the tool used to craft it.
- Places:
• `w_drop`: Weighted drop rates (must match the order of the drops list).
• `required_tooltier`: Format is ["type", tier] or null.
• `cost_tick:` How much "time" or stamina it costs to forage here.

---

## How to Run (Android)
1. Download **Termux** in F-Droid (Playstore is outdated)
2. Open Termux and setup it with:
```bash
> pkg update && pkg upgrade
```
- type 'Y' in: "Do you to continue [Y/n]"
- once done:
```bash
pkg install git python
```
- type 'Y' again in "Do you to continue [Y/n]"

3. After setup, type this:
```bash
> git clone [https://github.com/Eliteriz/Pieces-Of-Survival.git](https://github.com/Eliteriz/Pieces-Of-Survival.git)

> cd Pieces-Of-Survival

> python pos.py
```

## How to Run (PC - Windows, Linux, macOS)
1. Install **Python 3.10+** from [python.org](https://www.python.org/).
2. Open your Terminal (or PowerShell/CMD on Windows).
3. Clone and run:
```bash
> git clone [https://github.com/Eliteriz/Pieces-Of-Survival.git](https://github.com/Eliteriz/Pieces-Of-Survival.git)

> cd Pieces-Of-Survival

> python pos.py
```

---

### Upcoming updates:
- NPCs and more items/places
- More features
- Day & Night cycle and Enemies
- Combat System