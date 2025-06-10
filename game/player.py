"""
Player class for the dungeon crawler
"""

import pygame
from typing import Tuple
from .constants import PLAYER_COLOR, STARTING_HEALTH, STARTING_GOLD, HEX_RADIUS
from .hex_grid import HexGrid

class Player:
    """Player character class"""
    
    def __init__(self, start_q: int, start_r: int):
        self.q = start_q  # Hex coordinate q
        self.r = start_r  # Hex coordinate r
        self.health = STARTING_HEALTH
        self.max_health = STARTING_HEALTH
        self.gold = STARTING_GOLD
        self.floor = 1
        
        # Animation/movement
        self.is_moving = False
        self.move_timer = 0.0
        self.move_duration = 0.3
        self.start_pos = None
        self.target_pos = None
    
    def move_to(self, new_q: int, new_r: int, offset_x: int, offset_y: int):
        """Start moving to a new hex position"""
        if not self.is_moving:
            self.start_pos = HexGrid.hex_to_pixel(self.q, self.r, offset_x, offset_y)
            self.target_pos = HexGrid.hex_to_pixel(new_q, new_r, offset_x, offset_y)
            self.q = new_q
            self.r = new_r
            self.is_moving = True
            self.move_timer = 0.0
    
    def update(self, dt: float):
        """Update player state"""
        if self.is_moving:
            self.move_timer += dt
            if self.move_timer >= self.move_duration:
                self.is_moving = False
                self.move_timer = 0.0
    
    def get_render_position(self, offset_x: int, offset_y: int) -> Tuple[int, int]:
        """Get current render position (interpolated during movement)"""
        if not self.is_moving:
            return HexGrid.hex_to_pixel(self.q, self.r, offset_x, offset_y)
        
        # Interpolate between start and target positions
        progress = min(self.move_timer / self.move_duration, 1.0)
        
        # Smooth easing function
        progress = progress * progress * (3.0 - 2.0 * progress)
        
        start_x, start_y = self.start_pos
        target_x, target_y = self.target_pos
        
        current_x = start_x + (target_x - start_x) * progress
        current_y = start_y + (target_y - start_y) * progress
        
        return int(current_x), int(current_y)
    
    def take_damage(self, damage: int):
        """Take damage and return True if player dies"""
        self.health = max(0, self.health - damage)
        return self.health <= 0
    
    def heal(self, amount: int):
        """Heal the player"""
        self.health = min(self.max_health, self.health + amount)
    
    def collect_gold(self, amount: int):
        """Collect gold"""
        self.gold += amount
    
    def go_to_next_floor(self):
        """Move to the next floor"""
        self.floor += 1
        # Increase max health slightly each floor
        self.max_health += 10
        self.health = self.max_health
    
    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        """Render the player"""
        x, y = self.get_render_position(offset_x, offset_y)
        
        # Draw player as a circle
        pygame.draw.circle(screen, PLAYER_COLOR, (x, y), HEX_RADIUS // 2)
        
        # Draw health indicator (small bar above player)
        if self.health < self.max_health:
            bar_width = HEX_RADIUS
            bar_height = 4
            bar_x = x - bar_width // 2
            bar_y = y - HEX_RADIUS - 10
            
            # Background (red)
            pygame.draw.rect(screen, (255, 0, 0), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Health (green)
            health_width = int(bar_width * (self.health / self.max_health))
            pygame.draw.rect(screen, (0, 255, 0), 
                           (bar_x, bar_y, health_width, bar_height))
