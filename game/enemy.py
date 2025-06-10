"""
Enemy classes and combat system
"""

import random
import pygame
from typing import Tuple, List, Optional
from .constants import *
from .hex_grid import HexGrid

class Enemy:
    """Base enemy class with AI behavior"""
    
    def __init__(self, q: int, r: int, enemy_type: str = "goblin"):
        self.q = q
        self.r = r
        self.enemy_type = enemy_type
        self.alive = True
        
        # Set stats based on enemy type
        self._set_stats()
        
        # Visual
        self.color = RED
        self.size = HEX_RADIUS // 3
        
        # AI behavior
        self.state = "wandering"  # "wandering", "chasing", "idle"
        self.detection_range = 3  # How far enemy can see player
        self.chase_range = 5  # How far enemy will chase player
        self.last_known_player_pos = None
        self.wander_direction = random.randint(0, 5)  # Random initial direction
        self.turns_since_move = 0  # Track turns for movement frequency
        
    def _set_stats(self):
        """Set enemy stats based on type"""
        enemy_stats = {
            "goblin": {"health": 20, "attack": 8, "defense": 2, "gold": 15, "color": RED},
            "orc": {"health": 35, "attack": 12, "defense": 4, "gold": 25, "color": (150, 0, 0)},
            "skeleton": {"health": 15, "attack": 10, "defense": 1, "gold": 10, "color": (200, 200, 200)},
            "troll": {"health": 60, "attack": 18, "defense": 8, "gold": 50, "color": (100, 50, 0)},
        }
        
        stats = enemy_stats.get(self.enemy_type, enemy_stats["goblin"])
        self.max_health = stats["health"]
        self.health = self.max_health
        self.attack = stats["attack"]
        self.defense = stats["defense"]
        self.gold_reward = stats["gold"]
        self.color = stats["color"]
        
        # Set different move frequencies and behaviors for enemy types
        behavior_stats = {
            "goblin": {"move_frequency": 2, "detection_range": 2, "chase_range": 4},
            "orc": {"move_frequency": 3, "detection_range": 3, "chase_range": 5},
            "skeleton": {"move_frequency": 1, "detection_range": 4, "chase_range": 6},
            "troll": {"move_frequency": 4, "detection_range": 2, "chase_range": 3},
        }
        
        behavior = behavior_stats.get(self.enemy_type, behavior_stats["goblin"])
        self.move_frequency = behavior["move_frequency"]  # Turns between moves
        self.detection_range = behavior["detection_range"]
        self.chase_range = behavior["chase_range"]
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage dealt"""
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health -= actual_damage
        
        if self.health <= 0:
            self.health = 0
            self.alive = False
        
        return actual_damage
    
    def attack_player(self, player) -> int:
        """Attack the player and return damage dealt"""
        base_damage = self.attack + random.randint(-2, 2)  # Some randomness
        return max(1, base_damage)
    
    def get_combat_info(self) -> str:
        """Get combat information string"""
        return f"{self.enemy_type.title()} (HP: {self.health}/{self.max_health}, ATK: {self.attack}, DEF: {self.defense})"
    
    def process_turn(self, player_q: int, player_r: int, dungeon) -> Optional[Tuple[int, int]]:
        """Process enemy turn and return new position if moved"""
        if not self.alive:
            return None
        
        self.turns_since_move += 1
        
        # Check if it's time to move based on enemy type frequency
        if self.turns_since_move >= self.move_frequency:
            self.turns_since_move = 0
            
            # Calculate distance to player
            distance_to_player = HexGrid.hex_distance(self.q, self.r, player_q, player_r)
            
            # State transitions
            if distance_to_player <= self.detection_range:
                self.state = "chasing"
                self.last_known_player_pos = (player_q, player_r)
            elif self.state == "chasing" and distance_to_player > self.chase_range:
                self.state = "wandering"
                self.last_known_player_pos = None
            
            # Behavior based on state
            new_pos = None
            if self.state == "chasing":
                new_pos = self._chase_behavior(player_q, player_r, dungeon)
            elif self.state == "wandering":
                new_pos = self._wander_behavior(dungeon, player_q, player_r)
            
            return new_pos
        
        return None
    
    def _chase_behavior(self, player_q: int, player_r: int, dungeon) -> Optional[Tuple[int, int]]:
        """Chase the player"""
        # Get all possible moves
        neighbors = HexGrid.get_hex_neighbors(self.q, self.r)
        valid_moves = []
        
        for nq, nr in neighbors:
            if self._can_move_to(nq, nr, dungeon, player_q, player_r):
                # Calculate distance to player from this position
                distance = HexGrid.hex_distance(nq, nr, player_q, player_r)
                valid_moves.append((nq, nr, distance))
        
        if valid_moves:
            # Move to position closest to player
            valid_moves.sort(key=lambda x: x[2])
            best_move = valid_moves[0]
            return (best_move[0], best_move[1])
        
        return None
    
    def _wander_behavior(self, dungeon, player_q: int = None, player_r: int = None) -> Optional[Tuple[int, int]]:
        """Wander randomly around the dungeon"""
        neighbors = HexGrid.get_hex_neighbors(self.q, self.r)
        
        # Try to continue in the same direction first
        if self.wander_direction < len(neighbors):
            target_q, target_r = neighbors[self.wander_direction]
            if self._can_move_to(target_q, target_r, dungeon, player_q, player_r):
                return (target_q, target_r)
        
        # If can't continue, try random directions
        random.shuffle(neighbors)
        for nq, nr in neighbors:
            if self._can_move_to(nq, nr, dungeon, player_q, player_r):
                # Update wander direction
                self.wander_direction = neighbors.index((nq, nr))
                return (nq, nr)
        
        return None
    
    def _can_move_to(self, q: int, r: int, dungeon, player_q: int = None, player_r: int = None) -> bool:
        """Check if enemy can move to this position"""
        # Can't move to walls
        if not dungeon.is_walkable(q, r):
            return False
        
        # Can't move to positions with other enemies
        if dungeon.has_enemy(q, r) and (q, r) != (self.q, self.r):
            return False
        
        # Can't move into player's tile
        if player_q is not None and player_r is not None:
            if q == player_q and r == player_r:
                return False
        
        return True
    
    def move_to(self, new_q: int, new_r: int):
        """Move enemy to new position"""
        self.q = new_q
        self.r = new_r
    
    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        """Render the enemy with ASCII character"""
        if not self.alive:
            return
            
        x, y = HexGrid.hex_to_pixel(self.q, self.r, offset_x, offset_y)
        
        # ASCII symbols for different enemy types
        symbols = {
            "goblin": "g",
            "orc": "o", 
            "skeleton": "s",
            "troll": "T"
        }
        
        symbol = symbols.get(self.enemy_type, "?")
        
        # Use a font for ASCII rendering
        font = pygame.font.Font(None, 48)
        text_surface = font.render(symbol, True, self.color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)
        
        # Draw health bar if damaged
        if self.health < self.max_health:
            bar_width = HEX_RADIUS
            bar_height = 3
            bar_x = x - bar_width // 2
            bar_y = y - HEX_RADIUS - 5
            
            # Background (dark)
            pygame.draw.rect(screen, (50, 20, 20), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Health (enemy color)
            health_width = int(bar_width * (self.health / self.max_health))
            pygame.draw.rect(screen, self.color, 
                           (bar_x, bar_y, health_width, bar_height))

class CombatSystem:
    """Handles combat between player and enemies"""
    
    @staticmethod
    def initiate_combat(player, enemy) -> dict:
        """Start combat between player and enemy, return combat result"""
        combat_log = []
        
        # Combat continues until one dies
        while player.health > 0 and enemy.alive:
            # Player attacks first
            player_damage = CombatSystem._calculate_player_damage(player)
            actual_damage = enemy.take_damage(player_damage)
            combat_log.append(f"You deal {actual_damage} damage to {enemy.enemy_type}")
            
            if not enemy.alive:
                # Enemy defeated
                gold_gained = enemy.gold_reward
                player.collect_gold(gold_gained)
                combat_log.append(f"{enemy.enemy_type.title()} defeated! Gained {gold_gained} gold")
                break
            
            # Enemy attacks back
            enemy_damage = enemy.attack_player(player)
            player.take_damage(enemy_damage)
            combat_log.append(f"{enemy.enemy_type.title()} deals {enemy_damage} damage to you")
            
            if player.health <= 0:
                combat_log.append("You have been defeated!")
                break
        
        return {
            "log": combat_log,
            "player_won": enemy.alive == False,
            "player_died": player.health <= 0
        }
    
    @staticmethod
    def _calculate_player_damage(player) -> int:
        """Calculate player damage (can be enhanced with weapons later)"""
        base_damage = 15 + (player.floor - 1) * 2  # Damage scales with floor
        return base_damage + random.randint(-3, 3)  # Some randomness

def create_enemy_for_floor(floor: int) -> str:
    """Create appropriate enemy type for the given floor"""
    if floor == 1:
        return random.choice(["goblin", "skeleton"])
    elif floor <= 3:
        return random.choice(["goblin", "skeleton", "orc"])
    elif floor <= 5:
        return random.choice(["orc", "skeleton", "troll"])
    else:
        return random.choice(["orc", "troll", "troll"])  # More trolls on deeper floors
