"""
ASCII-style retro renderer for the dungeon crawler
"""

import pygame
from typing import Tuple, Dict
from .constants import *
from .hex_grid import HexGrid

class ASCIIRenderer:
    """Handles ASCII-style rendering with retro aesthetics"""
    
    def __init__(self):
        # Initialize fonts
        self.tile_font = pygame.font.Font(None, 48)  # Large font for tiles
        self.ui_font = pygame.font.Font(None, 32)    # Medium font for UI
        self.small_font = pygame.font.Font(None, 24) # Small font for details
        
        # ASCII symbols for different elements
        self.symbols = {
            TILE_FLOOR: ".",
            TILE_WALL: "#",
            TILE_STAIRS_DOWN: ">",
            TILE_STAIRS_UP: "<",
            TILE_GOLD: "$",
            "player": "@",
            "goblin": "g",
            "orc": "o", 
            "skeleton": "s",
            "troll": "T",
            "unknown": " ",
            "explored_empty": "·"  # Dimmed floor
        }
        
        # Color scheme - retro terminal colors
        self.colors = {
            TILE_FLOOR: (100, 100, 100),      # Dark gray
            TILE_WALL: (200, 200, 200),       # Light gray
            TILE_STAIRS_DOWN: (100, 150, 255), # Light blue
            TILE_STAIRS_UP: (100, 255, 100),   # Light green
            TILE_GOLD: (255, 215, 0),          # Gold
            "player": (255, 255, 255),         # White
            "goblin": (255, 100, 100),         # Light red
            "orc": (200, 50, 50),              # Dark red
            "skeleton": (220, 220, 220),       # Off-white
            "troll": (139, 69, 19),            # Brown
            "background": (20, 20, 30),        # Dark blue-black
            "ui_text": (200, 200, 200),        # Light gray
            "ui_accent": (100, 200, 255),      # Cyan
            "explored": (60, 60, 60),          # Very dark gray
            "preview": (80, 80, 100),          # Dark blue-gray
            "error": (255, 100, 100),          # Red for errors
            "success": (100, 255, 150),        # Green for success
            "warning": (255, 200, 100),        # Yellow for warnings
            "ui_panel": (25, 25, 35),          # Dark panel background
            "gold": (255, 215, 0),             # Gold color for gold messages
            "damage_dealt": (255, 150, 100),   # Orange for damage dealt
            "damage_received": (255, 100, 100), # Red for damage received
            "heal": (100, 255, 100),           # Green for healing
        }
    
    def render_tile(self, screen: pygame.Surface, x: int, y: int, tile_type: int, 
                   fog_state: str = "visible"):
        """Render a single tile with ASCII symbol"""
        symbol = self.symbols.get(tile_type, "?")
        
        # Determine color based on fog state
        if fog_state == "visible":
            color = self.colors.get(tile_type, WHITE)
        elif fog_state == "explored":
            color = self.colors["explored"]
            if tile_type == TILE_FLOOR:
                symbol = self.symbols["explored_empty"]
        elif fog_state == "preview":
            color = self.colors["preview"]
        else:  # unknown
            return  # Don't render unknown tiles
        
        # Render background hex
        vertices = HexGrid.get_hex_vertices(x, y)
        bg_color = self.colors["background"]
        if fog_state == "visible":
            bg_color = tuple(min(255, c + 10) for c in bg_color)  # Slightly lighter
        
        pygame.draw.polygon(screen, bg_color, vertices)
        pygame.draw.polygon(screen, color, vertices, 1)
        
        # Render ASCII symbol
        text_surface = self.tile_font.render(symbol, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)
    
    def render_entity_with_effects(self, screen: pygame.Surface, x: int, y: int, entity_type: str, effects: dict = None):
        """Render entity with visual effects"""
        effects = effects or {}
        
        # Get base color
        color = self.colors.get(entity_type, (255, 255, 255))
        
        # Apply effects
        if effects.get('anticipation', False):
            # Slightly brighten during anticipation
            color = tuple(min(255, int(c * 1.2)) for c in color)
        
        if effects.get('hit_flash', False):
            # Flash white when hit
            color = (255, 255, 255)
        
        if effects.get('critical', False):
            # Yellow tint for critical hits
            color = (255, 255, 100)
        
        # Render with effects
        self.render_entity(screen, x, y, entity_type, color)
    
    def render_entity(self, screen: pygame.Surface, x: int, y: int, entity_type: str, color_override=None):
        """Render an entity (player, enemy) with ASCII symbol"""
        symbol = self.symbols.get(entity_type, "?")
        color = color_override if color_override else self.colors.get(entity_type, WHITE)
        
        # Render with slight background for visibility
        bg_vertices = HexGrid.get_hex_vertices(x, y)
        pygame.draw.polygon(screen, (0, 0, 0, 100), bg_vertices)
        
        text_surface = self.tile_font.render(symbol, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)
    
    def render_ui_panel(self, screen: pygame.Surface, x: int, y: int, width: int, height: int):
        """Render a UI panel with retro border"""
        # Main panel
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (10, 10, 20), panel_rect)
        pygame.draw.rect(screen, self.colors["ui_accent"], panel_rect, 2)
        
        # Corner decorations
        corner_size = 8
        corners = [
            (x, y), (x + width - corner_size, y),
            (x, y + height - corner_size), (x + width - corner_size, y + height - corner_size)
        ]
        
        for corner_x, corner_y in corners:
            pygame.draw.rect(screen, self.colors["ui_accent"], 
                           (corner_x, corner_y, corner_size, corner_size))
    
    def render_text(self, screen: pygame.Surface, text: str, x: int, y: int, 
                   font_size: str = "ui", color: str = "ui_text"):
        """Render text with specified font and color"""
        font = {
            "tile": self.tile_font,
            "ui": self.ui_font,
            "small": self.small_font
        }.get(font_size, self.ui_font)
        
        text_color = self.colors.get(color, self.colors["ui_text"])
        text_surface = font.render(text, True, text_color)
        screen.blit(text_surface, (x, y))
        return text_surface.get_rect(x=x, y=y)
    
    def render_health_bar(self, screen: pygame.Surface, x: int, y: int, 
                         current: int, maximum: int, width: int = 100):
        """Render a retro-style health bar"""
        height = 8
        
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (50, 20, 20), bg_rect)
        pygame.draw.rect(screen, self.colors["ui_text"], bg_rect, 1)
        
        # Health fill
        if maximum > 0:
            fill_width = int(width * (current / maximum))
            fill_rect = pygame.Rect(x + 1, y + 1, fill_width - 2, height - 2)
            
            # Color based on health percentage
            health_percent = current / maximum
            if health_percent > 0.6:
                fill_color = (100, 200, 100)  # Green
            elif health_percent > 0.3:
                fill_color = (200, 200, 100)  # Yellow
            else:
                fill_color = (200, 100, 100)  # Red
            
            pygame.draw.rect(screen, fill_color, fill_rect)
    
    def render_message_panel(self, screen: pygame.Surface, message: str, message_type: str = "info"):
        """Render a non-intrusive message panel"""
        if not message:
            return
        
        # Position at top-right, below status panel
        panel_width = min(400, max(200, len(message) * 8 + 40))
        panel_height = 50
        panel_x = SCREEN_WIDTH - panel_width - 10
        panel_y = 150  # Below status panel
        
        # Different colors for different message types
        colors = {
            "info": self.colors["ui_text"],
            "success": self.colors["ui_accent"],
            "warning": (255, 200, 100),
            "error": (255, 100, 100),
            "combat": (255, 150, 150)
        }
        
        message_color = colors.get(message_type, self.colors["ui_text"])
        
        # Semi-transparent background
        bg_surface = pygame.Surface((panel_width, panel_height))
        bg_surface.set_alpha(200)
        bg_surface.fill((20, 20, 30))
        screen.blit(bg_surface, (panel_x, panel_y))
        
        # Border
        pygame.draw.rect(screen, message_color, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Message text
        self.render_text(screen, message, panel_x + 10, panel_y + 15, "small", message_color)
    
    def render_floating_text(self, screen: pygame.Surface, text: str, x: int, y: int, 
                           color: str = "ui_accent", fade_alpha: float = 1.0, animation_type: str = "float"):
        """Render floating text with fade effect and animation-specific styling"""
        if fade_alpha <= 0:
            return
        
        # Choose font based on animation type
        if animation_type == "damage":
            font = self.ui_font  # Larger font for damage numbers
        else:
            font = self.small_font
        
        # Get color
        text_color = self.colors.get(color, self.colors["ui_text"])
        
        # Create text surface
        text_surface = font.render(text, True, text_color)
        
        # Apply fade
        if fade_alpha < 1.0:
            text_surface.set_alpha(int(255 * fade_alpha))
        
        # Add outline for damage numbers to make them more visible
        if animation_type == "damage":
            # Create outline
            outline_surface = font.render(text, True, (0, 0, 0))
            if fade_alpha < 1.0:
                outline_surface.set_alpha(int(255 * fade_alpha))
            
            # Draw outline in multiple positions
            text_rect = text_surface.get_rect(center=(x, y))
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                outline_rect = text_rect.copy()
                outline_rect.x += dx
                outline_rect.y += dy
                screen.blit(outline_surface, outline_rect)
        
        # Draw main text
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)
    
    def render_combat_log_panel(self, screen: pygame.Surface, combat_log: list):
        """Render combat log with retro styling"""
        if not combat_log:
            return
        
        panel_width = 350
        panel_height = len(combat_log) * 25 + 40
        panel_x = SCREEN_WIDTH - panel_width - 10
        panel_y = 10
        
        # Render panel
        self.render_ui_panel(screen, panel_x, panel_y, panel_width, panel_height)
        
        # Title
        self.render_text(screen, "COMBAT LOG", panel_x + 10, panel_y + 10, "ui", "ui_accent")
        
        # Log entries
        for i, entry in enumerate(combat_log):
            self.render_text(screen, entry, panel_x + 10, panel_y + 35 + i * 20, "small")
    
    def render_status_panel(self, screen: pygame.Surface, player, god_mode: bool = False):
        """Render player status panel"""
        panel_width = 250
        panel_height = 140 if god_mode else 120
        panel_x = 10
        panel_y = 10
        
        # Render panel
        self.render_ui_panel(screen, panel_x, panel_y, panel_width, panel_height)
        
        # Player symbol
        self.render_text(screen, "@", panel_x + 15, panel_y + 15, "tile", "player")
        
        # Stats
        y_offset = panel_y + 20
        self.render_text(screen, f"HEALTH:", panel_x + 50, y_offset, "small", "ui_text")
        self.render_health_bar(screen, panel_x + 120, y_offset + 2, player.health, player.max_health)
        
        y_offset += 25
        self.render_text(screen, f"GOLD: {player.gold}", panel_x + 50, y_offset, "small", "ui_accent")
        
        y_offset += 20
        self.render_text(screen, f"FLOOR: {player.floor}", panel_x + 50, y_offset, "small", "ui_text")
        
        attack_power = 15 + (player.floor - 1) * 2
        y_offset += 20
        self.render_text(screen, f"ATTACK: {attack_power}", panel_x + 50, y_offset, "small", "ui_text")
        
        # God mode indicator
        if god_mode:
            y_offset += 20
            self.render_text(screen, "GOD MODE: ON", panel_x + 50, y_offset, "small", "ui_accent")
