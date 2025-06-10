"""
Fog of War system for the dungeon crawler
"""

import pygame
from typing import Set, Tuple, Dict
from .constants import *
from .hex_grid import HexGrid

class FogOfWar:
    """Manages visibility and fog of war"""
    
    def __init__(self):
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.visible_tiles: Set[Tuple[int, int]] = set()
        self.player_vision_range = 3
        
    def update_visibility(self, player_q: int, player_r: int, dungeon):
        """Update which tiles are currently visible"""
        self.visible_tiles.clear()
        
        # Add player position
        self.visible_tiles.add((player_q, player_r))
        self.explored_tiles.add((player_q, player_r))
        
        # Use a more comprehensive visibility algorithm
        # Check all tiles within vision range
        for distance in range(1, self.player_vision_range + 1):
            for check_q in range(player_q - distance, player_q + distance + 1):
                for check_r in range(player_r - distance, player_r + distance + 1):
                    # Skip if outside vision range
                    actual_distance = HexGrid.hex_distance(player_q, player_r, check_q, check_r)
                    if actual_distance > self.player_vision_range:
                        continue
                    
                    # Check line of sight
                    if self._has_line_of_sight(player_q, player_r, check_q, check_r, dungeon):
                        self.visible_tiles.add((check_q, check_r))
                        self.explored_tiles.add((check_q, check_r))
        
        # Add adjacent unexplored tiles for preview (to prevent blind exploration)
        self._add_adjacent_preview_tiles(player_q, player_r)
    
    def _add_adjacent_preview_tiles(self, player_q: int, player_r: int):
        """Add adjacent unexplored tiles to visible set for preview"""
        neighbors = HexGrid.get_hex_neighbors(player_q, player_r)
        for nq, nr in neighbors:
            if (nq, nr) not in self.explored_tiles:
                self.visible_tiles.add((nq, nr))  # Show but don't mark as explored
    
    def _get_tiles_at_distance(self, center_q: int, center_r: int, distance: int) -> Set[Tuple[int, int]]:
        """Get all tiles at a specific distance from center"""
        tiles = set()
        
        if distance == 0:
            return {(center_q, center_r)}
        
        # Use proper hex ring algorithm
        # Start at one corner of the ring and walk around
        q, r = center_q - distance, center_r
        
        # Six directions for hexagonal movement
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        
        for i, (dq, dr) in enumerate(directions):
            for step in range(distance):
                tiles.add((q, r))
                q += dq
                r += dr
        
        return tiles
    
    def _has_line_of_sight(self, start_q: int, start_r: int, end_q: int, end_r: int, dungeon) -> bool:
        """Check if there's a clear line of sight between two points"""
        distance = HexGrid.hex_distance(start_q, start_r, end_q, end_r)
        
        if distance <= 1:
            return True
        
        # Use hex line algorithm with proper interpolation
        for i in range(1, distance):
            # Linear interpolation parameter
            t = i / distance
            
            # Interpolate in axial coordinates
            lerp_q = start_q + (end_q - start_q) * t
            lerp_r = start_r + (end_r - start_r) * t
            
            # Round to nearest hex
            check_q, check_r = HexGrid.hex_round(lerp_q, lerp_r)
            
            # Check if this tile blocks vision (walls block vision)
            if dungeon.get_tile(check_q, check_r) == TILE_WALL:
                return False
        
        return True
    
    def is_visible(self, q: int, r: int) -> bool:
        """Check if a tile is currently visible"""
        return (q, r) in self.visible_tiles
    
    def is_explored(self, q: int, r: int) -> bool:
        """Check if a tile has been explored"""
        return (q, r) in self.explored_tiles
    
    def is_preview_only(self, q: int, r: int) -> bool:
        """Check if a tile is only visible as preview (adjacent unexplored)"""
        return (q, r) in self.visible_tiles and (q, r) not in self.explored_tiles
    
    def render_fog(self, screen: pygame.Surface, dungeon, offset_x: int, offset_y: int):
        """Render fog of war overlay"""
        # Create a surface for the fog
        fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fog_surface.set_alpha(180)  # Semi-transparent
        fog_surface.fill(BLACK)
        
        # Cut out holes for visible and explored areas
        for (q, r) in self.explored_tiles:
            x, y = HexGrid.hex_to_pixel(q, r, offset_x, offset_y)
            vertices = HexGrid.get_hex_vertices(x, y)
            
            if self.is_visible(q, r):
                # Fully visible - no fog
                pygame.draw.polygon(fog_surface, (0, 0, 0, 0), vertices)
            else:
                # Explored but not visible - light fog
                pygame.draw.polygon(fog_surface, (0, 0, 0, 100), vertices)
        
        # Apply fog to screen
        screen.blit(fog_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
