"""
Dungeon generation and management
"""

import random
import pygame
from typing import Dict, Tuple, List, Optional
from .constants import *
from .hex_grid import HexGrid
from .enemy import Enemy, create_enemy_for_floor
from .nuclear_throne_generator import NuclearThroneGenerator

class Dungeon:
    """Dungeon floor with hexagonal grid"""
    
    def __init__(self, width: int, height: int, floor_number: int):
        self.width = width
        self.height = height
        self.floor_number = floor_number
        self.tiles: Dict[Tuple[int, int], int] = {}
        self.enemies: Dict[Tuple[int, int], Enemy] = {}
        self.player_start: Optional[Tuple[int, int]] = None
        self.stairs_down: Optional[Tuple[int, int]] = None
        
        self.generate_dungeon()
    
    def generate_dungeon(self):
        """Generate dungeon using Nuclear Throne-style algorithm"""
        generator = NuclearThroneGenerator(self.width, self.height)
        self.tiles, self.player_start = generator.generate(self.floor_number)
        
        # Find stairs position
        for pos, tile_type in self.tiles.items():
            if tile_type == TILE_STAIRS_DOWN:
                self.stairs_down = pos
                break
        
        # Place enemies on floor tiles (away from player start)
        self._place_enemies()
    
    def _place_enemies(self):
        """Place enemies on the generated floor"""
        floor_tiles = [(q, r) for (q, r), tile_type in self.tiles.items() 
                      if tile_type == TILE_FLOOR]
        
        # Remove tiles too close to player start
        if self.player_start:
            safe_distance = 3
            floor_tiles = [(q, r) for (q, r) in floor_tiles 
                          if HexGrid.hex_distance(q, r, self.player_start[0], self.player_start[1]) >= safe_distance]
        
        # Place enemies (more on higher floors)
        num_enemies = random.randint(2, 4 + self.floor_number // 2)
        enemy_positions = random.sample(floor_tiles, min(num_enemies, len(floor_tiles)))
        
        for pos in enemy_positions:
            enemy_type = create_enemy_for_floor(self.floor_number)
            self.enemies[pos] = Enemy(pos[0], pos[1], enemy_type)
    
    def get_tile(self, q: int, r: int) -> int:
        """Get tile type at position"""
        return self.tiles.get((q, r), TILE_WALL)
    
    def is_walkable(self, q: int, r: int) -> bool:
        """Check if a tile is walkable"""
        tile_type = self.get_tile(q, r)
        # Can walk on floors, stairs, gold, and tiles with enemies
        return tile_type in [TILE_FLOOR, TILE_STAIRS_DOWN, TILE_STAIRS_UP, TILE_GOLD] or (q, r) in self.enemies
    
    def has_enemy(self, q: int, r: int) -> bool:
        """Check if there's an enemy at this position"""
        return (q, r) in self.enemies and self.enemies[(q, r)].alive
    
    def get_enemy(self, q: int, r: int) -> Optional[Enemy]:
        """Get enemy at position"""
        return self.enemies.get((q, r))
    
    def interact_with_tile(self, q: int, r: int, player) -> str:
        """Interact with a tile and return a message"""
        # Check for enemy first
        if self.has_enemy(q, r):
            return "enemy"
        
        tile_type = self.get_tile(q, r)
        
        if tile_type == TILE_GOLD:
            gold_amount = random.randint(10, 30) * self.floor_number
            player.collect_gold(gold_amount)
            self.tiles[(q, r)] = TILE_FLOOR
            return f"Found {gold_amount} gold!"
        
        elif tile_type == TILE_STAIRS_DOWN:
            return "stairs_down"
        
        return ""
    
    def process_enemy_turns(self, player_q: int, player_r: int):
        """Process all enemy turns (turn-based)"""
        enemies_to_move = []
        
        for pos, enemy in self.enemies.items():
            if enemy.alive:
                new_pos = enemy.process_turn(player_q, player_r, self)
                if new_pos and new_pos != pos:
                    enemies_to_move.append((pos, new_pos, enemy))
        
        # Move enemies to new positions
        for old_pos, new_pos, enemy in enemies_to_move:
            # Remove from old position
            del self.enemies[old_pos]
            # Move enemy
            enemy.move_to(new_pos[0], new_pos[1])
            # Add to new position
            self.enemies[new_pos] = enemy
    
    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int, fog_of_war=None, ascii_renderer=None):
        """Render the dungeon"""
        # Render tiles
        for (q, r), tile_type in self.tiles.items():
            x, y = HexGrid.hex_to_pixel(q, r, offset_x, offset_y)
            
            # Determine fog state
            fog_state = "unknown"
            if fog_of_war:
                if fog_of_war.is_visible(q, r):
                    if fog_of_war.is_explored(q, r):
                        fog_state = "visible"
                    else:
                        fog_state = "preview"
                elif fog_of_war.is_explored(q, r):
                    fog_state = "explored"
            else:
                fog_state = "visible"
            
            # Skip unknown tiles
            if fog_state == "unknown":
                continue
            
            # Use ASCII renderer if available
            if ascii_renderer:
                ascii_renderer.render_tile(screen, x, y, tile_type, fog_state)
            else:
                # Fallback to old rendering
                vertices = HexGrid.get_hex_vertices(x, y)
                color = TILE_COLORS.get(tile_type, BLACK)
                
                if fog_state == "explored":
                    color = tuple(c // 3 for c in color)
                elif fog_state == "preview":
                    color = tuple(c // 2 for c in color)
                
                pygame.draw.polygon(screen, color, vertices)
                pygame.draw.polygon(screen, BLACK, vertices, 2)
        
        # Render enemies (only visible ones)
        for enemy in self.enemies.values():
            if enemy.alive and fog_of_war and fog_of_war.is_visible(enemy.q, enemy.r):
                x, y = HexGrid.hex_to_pixel(enemy.q, enemy.r, offset_x, offset_y)
                
                if ascii_renderer:
                    ascii_renderer.render_entity(screen, x, y, enemy.enemy_type)
                else:
                    enemy.render(screen, offset_x, offset_y)
                enemy.render(screen, offset_x, offset_y)
