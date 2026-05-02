import threading
import time
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from helpers import game_config as config
from helpers import game_utils as utils


@dataclass
class CombatState:
    """Represents the state of a combat encounter"""
    player: any  # Player object
    enemy_name: str
    enemy_health: int
    enemy_max_health: int
    player_health: int
    player_charge: int = 0
    player_attack_cooldown: float = 0.0
    enemy_attack_cooldown: float = 0.0
    combat_logs: List[str] = field(default_factory=list)
    is_running: bool = True
    player_won: bool = False
    fled: bool = False


class CombatEngine:
    """Real-time combat system with threading and simultaneous attacks"""
    
    def __init__(self, player, enemy_name: str):
        self.player = player
        self.enemy_name = enemy_name
        self.enemy_data = config.BESTIARY.get(enemy_name, {})
        
        self.state = CombatState(
            player=player,
            enemy_name=enemy_name,
            enemy_health=self.enemy_data.get("health", 10),
            enemy_max_health=self.enemy_data.get("health", 10),
            player_health=player.health
        )
        
        self.running = True
        self.update_thread = None
        self.enemy_ai_thread = None
        
    def get_player_weapon(self) -> Tuple[Optional[str], Dict]:
        """Get player's equipped weapon (first weapon in inventory)"""
        for item, qty in self.player.inventory.items():
            info = config.ITEMS.get(item, {})
            if info.get("category") == "Weapons" and qty > 0:
                return item, info
        return None, {}
    
    def add_log(self, message: str) -> None:
        """Add message to combat log with timestamp"""
        self.state.combat_logs.append(message)
        if len(self.state.combat_logs) > 10:
            self.state.combat_logs.pop(0)
    
    def start_combat_update_thread(self) -> None:
        """Start the real-time update thread (tick every 0.1s)"""
        def update_loop():
            while self.running and self.state.is_running:
                # Decrement cooldowns
                if self.state.player_attack_cooldown > 0:
                    self.state.player_attack_cooldown -= 0.1
                    self.state.player_attack_cooldown = max(0, self.state.player_attack_cooldown)
                
                if self.state.enemy_attack_cooldown > 0:
                    self.state.enemy_attack_cooldown -= 0.1
                    self.state.enemy_attack_cooldown = max(0, self.state.enemy_attack_cooldown)
                
                # Check win/lose conditions
                if self.state.enemy_health <= 0:
                    self.state.is_running = False
                    self.state.player_won = True
                    self.add_log(f"{config.GREEN}★ {self.enemy_name} defeated!{config.RESET}")
                    self.player.health = self.state.player_health
                    break
                
                if self.state.player_health <= 0:
                    self.state.is_running = False
                    self.add_log(f"{config.RED}★ You have been defeated!{config.RESET}")
                    self.player.health = 0
                    break
                
                time.sleep(0.1)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def start_enemy_ai_thread(self) -> None:
        """Start enemy AI thread for autonomous attacks"""
        def enemy_ai_loop():
            while self.running and self.state.is_running:
                if self.state.enemy_attack_cooldown <= 0:
                    self.enemy_attack()
                time.sleep(0.05)
        
        self.enemy_ai_thread = threading.Thread(target=enemy_ai_loop, daemon=True)
        self.enemy_ai_thread.start()
    
    def player_attack(self) -> str:
        """Player basic attack"""
        if self.state.player_attack_cooldown > 0:
            return f"{config.YELLOW}[Cooldown: {self.state.player_attack_cooldown:.1f}s]{config.RESET}"
        
        weapon_name, weapon_info = self.get_player_weapon()
        if not weapon_name:
            return f"{config.RED}No weapon equipped!{config.RESET}"
        
        damage = weapon_info.get("damage", 1)
        attack_speed = weapon_info.get("attack_speed", 1.0)
        pierce_chance = weapon_info.get("pierce_chance", 0.0)
        
        # Calculate damage with random variance
        variance = random.uniform(0.8, 1.2)
        final_damage = int(damage * variance)
        
        # Pierce chance reduces enemy armor
        enemy_armor = self.enemy_data.get("armor", 0)
        if random.random() < pierce_chance:
            final_damage = int(final_damage * 1.5)
            armor_text = f"{config.CYAN}(pierced armor!){config.RESET}"
        else:
            final_damage = max(1, final_damage - enemy_armor // 2)
            armor_text = ""
        
        self.state.enemy_health -= final_damage
        self.state.player_attack_cooldown = 1.0 / attack_speed
        
        self.add_log(f"You swung {weapon_name}! (-{final_damage} HP to {self.enemy_name}) {armor_text}")
        return f"{config.GREEN}Attack! (-{final_damage} HP){config.RESET}"
    
    def player_skill(self) -> str:
        """Player use charged skill"""
        if self.state.player_charge < 100:
            return f"{config.YELLOW}Skill not charged ({self.state.player_charge}/100){config.RESET}"
        
        weapon_name, weapon_info = self.get_player_weapon()
        if not weapon_name:
            return f"{config.RED}No weapon equipped!{config.RESET}"
        
        skill_name = weapon_info.get("charge_skill")
        if not skill_name:
            return f"{config.RED}No skill available!{config.RESET}"
        
        skill_info = config.WEAPON_SKILLS.get(skill_name, {})
        damage_mult = skill_info.get("damage_multiplier", 1.0)
        base_damage = weapon_info.get("damage", 1)
        
        final_damage = int(base_damage * damage_mult)
        self.state.enemy_health -= final_damage
        self.state.player_charge = 0
        self.state.player_attack_cooldown = 2.0
        
        self.add_log(f"{config.PURPLE}★ {skill_name}! (-{final_damage} HP to {self.enemy_name}){config.RESET}")
        return f"{config.PURPLE}Skill used! (-{final_damage} HP){config.RESET}"
    
    def player_charge(self) -> str:
        """Player build up charge"""
        charge_gain = 15
        self.state.player_charge = min(100, self.state.player_charge + charge_gain)
        self.add_log(f"You charge up! ({self.state.player_charge}/100)")
        return f"Charging... ({self.state.player_charge}/100)"
    
    def player_observe(self) -> str:
        """Observe enemy details"""
        enemy_hp_percent = (self.state.enemy_health / self.state.enemy_max_health) * 100
        hp_bar = self._get_hp_bar(self.state.enemy_health, self.state.enemy_max_health)
        
        skills = ", ".join(self.enemy_data.get("skills", []))
        return f"\n{config.CYAN}» {self.enemy_name} Details «{config.RESET}\nHealth: {hp_bar}\nDamage: {self.enemy_data.get('damage', 0)} | Speed: {self.enemy_data.get('attack_speed', 1.0)} | Armor: {self.enemy_data.get('armor', 0)}\nSkills: {skills}"
    
    def player_flee(self) -> bool:
        """Attempt to flee combat"""
        flee_chance = 0.4 + (self.player.health / 100) * 0.3
        if random.random() < flee_chance:
            self.state.fled = True
            self.state.is_running = False
            self.add_log(f"{config.YELLOW}You fled from combat!{config.RESET}")
            return True
        else:
            self.add_log(f"{config.RED}Failed to flee!{config.RESET}")
            return False
    
    def enemy_attack(self) -> None:
        """Enemy autonomous attack"""
        enemy_damage = self.enemy_data.get("damage", 1)
        enemy_speed = self.enemy_data.get("attack_speed", 1.0)
        skills = self.enemy_data.get("skills", [])
        
        # Randomly pick a skill or basic attack
        if random.random() < 0.3 and skills:
            skill = random.choice(skills)
            skill_info = config.ENEMY_SKILLS.get(skill, {})
            damage_mult = skill_info.get("damage_multiplier", 1.0)
            final_damage = int(enemy_damage * damage_mult)
            action_text = f"{skill}"
        else:
            final_damage = int(enemy_damage * random.uniform(0.8, 1.2))
            action_text = "attacked"
        
        self.state.player_health -= final_damage
        self.state.enemy_attack_cooldown = 1.0 / enemy_speed
        
        self.add_log(f"{self.enemy_name} {action_text}! (-{final_damage} HP to you)")
    
    def _get_hp_bar(self, current: int, maximum: int) -> str:
        """Generate ASCII health bar"""
        bars = int((current / maximum) * 10)
        bar = "█" * bars + "░" * (10 - bars)
        return f"[{bar}] {current}/{maximum}"
    
    def get_combat_display(self) -> str:
        """Get formatted combat screen"""
        player_hp_bar = self._get_hp_bar(self.state.player_health, self.player.health)
        enemy_hp_bar = self._get_hp_bar(self.state.enemy_health, self.state.enemy_max_health)
        weapon_name, weapon_info = self.get_player_weapon()
        skill_name = weapon_info.get("charge_skill", "N/A")
        
        display = f"\n{config.CYAN}------ ARENA ------{config.RESET}\n"
        display += f"{config.RED}{self.enemy_name}: {enemy_hp_bar}{config.RESET}\n"
        display += f"{config.GREEN}{self.player.name}: {player_hp_bar}{config.RESET}\n"
        display += f"\n{config.YELLOW}Combat Logs:{config.RESET}\n"
        
        for log in self.state.combat_logs[-5:]:
            display += f"- {log}\n"
        
        display += f"\n{config.CYAN}What to do in combat?{config.RESET}\n"
        display += f"[1]: Attack [Cooldown: {max(0, self.state.player_attack_cooldown):.1f}s]\n"
        display += f"[2]: {skill_name} [Charge: {self.state.player_charge}/100]\n"
        display += f"[3]: Observe {self.enemy_name}\n"
        display += f"[4]: Flee\n"
        
        return display
    
    def stop(self) -> None:
        """Stop combat threads"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        if self.enemy_ai_thread:
            self.enemy_ai_thread.join(timeout=1)
