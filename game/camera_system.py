"""
Enhanced camera system with smart centering and dramatic effects
"""

import math
from typing import Tuple, Optional
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager
from .hex_grid import HexGrid

class SmartCamera:
    """Enhanced camera with predictive movement and dramatic effects"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera position
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        
        # Camera movement
        self.follow_speed = 3.0
        self.prediction_strength = 0.3  # How much to lead the player
        self.smoothing = 0.85  # Camera smoothing factor
        
        # Player tracking
        self.player_q = 0
        self.player_r = 0
        self.last_player_q = 0
        self.last_player_r = 0
        self.movement_direction = (0.0, 0.0)
        
        # Dramatic effects
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.zoom_speed = 2.0
        
        # Camera shake integration
        self.base_x = 0.0
        self.base_y = 0.0
        
        # Subscribe to events
        game_events.subscribe(GameEventType.MOVE_START, self._on_move_start)
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.FLOOR_CHANGE, self._on_floor_change)
    
    def update(self, dt: float, player_q: int, player_r: int):
        """Update camera position with smart following"""
        if not juice_manager.settings.smart_camera_enabled or not juice_manager.settings.enabled:
            # Simple centering if smart camera disabled
            self._simple_center(player_q, player_r)
            return
        
        # Track player movement
        if player_q != self.player_q or player_r != self.player_r:
            self.last_player_q = self.player_q
            self.last_player_r = self.player_r
            self.player_q = player_q
            self.player_r = player_r
            
            # Calculate movement direction
            if self.last_player_q != 0 or self.last_player_r != 0:
                dx = player_q - self.last_player_q
                dy = player_r - self.last_player_r
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0:
                    self.movement_direction = (dx / length, dy / length)
        
        # Get player pixel position
        player_pixel_x, player_pixel_y = HexGrid.hex_to_pixel(player_q, player_r, 0, 0)
        
        # Calculate predictive offset
        prediction_offset_x = self.movement_direction[0] * 100 * self.prediction_strength
        prediction_offset_y = self.movement_direction[1] * 100 * self.prediction_strength
        
        # Target camera position (centered on player + prediction)
        self.target_x = self.screen_width // 2 - (player_pixel_x + prediction_offset_x)
        self.target_y = self.screen_height // 2 - (player_pixel_y + prediction_offset_y)
        
        # Smooth camera movement
        self.base_x += (self.target_x - self.base_x) * self.follow_speed * dt
        self.base_y += (self.target_y - self.base_y) * self.follow_speed * dt
        
        # Update zoom
        self.zoom_level += (self.target_zoom - self.zoom_level) * self.zoom_speed * dt
        
        # Apply zoom to final position
        self.x = self.base_x * self.zoom_level
        self.y = self.base_y * self.zoom_level
    
    def _simple_center(self, player_q: int, player_r: int):
        """Simple camera centering without smart features"""
        player_pixel_x, player_pixel_y = HexGrid.hex_to_pixel(player_q, player_r, 0, 0)
        self.target_x = self.screen_width // 2 - player_pixel_x
        self.target_y = self.screen_height // 2 - player_pixel_y
        self.x = self.target_x
        self.y = self.target_y
    
    def get_position(self) -> Tuple[int, int]:
        """Get current camera position"""
        return int(self.x), int(self.y)
    
    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.zoom_level
    
    def set_zoom(self, zoom: float, duration: float = 0.5):
        """Set target zoom level"""
        self.target_zoom = max(0.5, min(2.0, zoom))
    
    def focus_on_position(self, q: int, r: int, zoom: float = 1.2, duration: float = 1.0):
        """Focus camera on specific hex position"""
        if not juice_manager.settings.smart_camera_enabled:
            return
        
        pixel_x, pixel_y = HexGrid.hex_to_pixel(q, r, 0, 0)
        self.target_x = self.screen_width // 2 - pixel_x
        self.target_y = self.screen_height // 2 - pixel_y
        self.set_zoom(zoom, duration)
    
    def reset_zoom(self):
        """Reset zoom to normal"""
        self.target_zoom = 1.0
    
    def _on_move_start(self, event):
        """Handle movement start for camera prediction"""
        # Camera prediction is handled in update()
        pass
    
    def _on_attack_hit(self, event):
        """Handle attack hit for camera focus"""
        if not juice_manager.settings.smart_camera_enabled:
            return
        
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        damage = event.get('damage', 0)
        
        # Slight zoom in for big hits
        if damage >= 25:
            self.set_zoom(1.1, 0.3)
    
    def _on_enemy_death(self, event):
        """Handle enemy death for dramatic camera"""
        if not juice_manager.settings.smart_camera_enabled:
            return
        
        enemy_type = event.get('enemy_type', '')
        q = event.get('q', 0)
        r = event.get('r', 0)
        
        if 'boss' in enemy_type.lower():
            # Dramatic zoom out for boss death
            self.focus_on_position(q, r, 0.8, 2.0)
        else:
            # Brief focus on enemy death
            self.set_zoom(1.15, 0.5)
    
    def _on_floor_change(self, event):
        """Handle floor change camera effect"""
        # Reset zoom on floor change
        self.reset_zoom()

class LightingEffects:
    """Lighting and visual emphasis effects"""
    
    def __init__(self):
        # Focus flash effects
        self.focus_flashes = []
        
        # Vignette effects
        self.vignette_intensity = 0.0
        self.target_vignette = 0.0
        self.vignette_speed = 3.0
        
        # Color overlay effects
        self.color_overlay = (0, 0, 0)
        self.overlay_alpha = 0.0
        self.target_overlay_alpha = 0.0
        self.overlay_speed = 4.0
        
        # Subscribe to events
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ATTACK_CRIT, self._on_attack_crit)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.FLOOR_CHANGE, self._on_floor_change)
    
    def update(self, dt: float):
        """Update lighting effects"""
        if not juice_manager.settings.focus_flash_enabled or not juice_manager.settings.enabled:
            return
        
        # Update focus flashes
        for flash in self.focus_flashes[:]:
            flash['timer'] -= dt
            flash['intensity'] = max(0.0, flash['timer'] / flash['duration'])
            
            if flash['timer'] <= 0:
                self.focus_flashes.remove(flash)
        
        # Update vignette
        self.vignette_intensity += (self.target_vignette - self.vignette_intensity) * self.vignette_speed * dt
        
        # Update color overlay
        self.overlay_alpha += (self.target_overlay_alpha - self.overlay_alpha) * self.overlay_speed * dt
    
    def add_focus_flash(self, q: int, r: int, color: Tuple[int, int, int] = (255, 255, 255), 
                       intensity: float = 0.8, duration: float = 0.2):
        """Add a focus flash at hex position"""
        if not juice_manager.settings.focus_flash_enabled:
            return
        
        # Convert hex to world position
        from .hex_grid import HexGrid
        world_x, world_y = HexGrid.hex_to_pixel(q, r, 0, 0)
        
        self.focus_flashes.append({
            'world_x': world_x,  # Store world position
            'world_y': world_y,
            'color': color,
            'intensity': intensity * juice_manager.settings.intensity,
            'timer': duration,
            'duration': duration,
            'radius': 50
        })
    
    def set_vignette(self, intensity: float, duration: float = 0.5):
        """Set vignette intensity"""
        if not juice_manager.settings.focus_flash_enabled:
            return
        
        self.target_vignette = max(0.0, min(1.0, intensity * juice_manager.settings.intensity))
    
    def set_color_overlay(self, color: Tuple[int, int, int], alpha: float, duration: float = 0.5):
        """Set color overlay effect"""
        if not juice_manager.settings.focus_flash_enabled:
            return
        
        self.color_overlay = color
        self.target_overlay_alpha = max(0.0, min(1.0, alpha * juice_manager.settings.intensity))
    
    def get_focus_flashes(self) -> list:
        """Get current focus flashes for rendering"""
        return self.focus_flashes.copy()
    
    def get_vignette_data(self) -> dict:
        """Get vignette data for rendering"""
        if self.vignette_intensity > 0.01:
            return {
                'intensity': self.vignette_intensity,
                'color': (0, 0, 0)
            }
        return None
    
    def get_color_overlay_data(self) -> dict:
        """Get color overlay data for rendering"""
        if self.overlay_alpha > 0.01:
            return {
                'color': self.color_overlay,
                'alpha': self.overlay_alpha
            }
        return None
    
    def _on_attack_hit(self, event):
        """Handle attack hit flash"""
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        damage = event.get('damage', 0)
        
        # Flash the struck enemy
        flash_intensity = min(0.8, 0.3 + damage * 0.02)
        self.add_focus_flash(target_q, target_r, (255, 255, 255), flash_intensity, 0.15)
    
    def _on_attack_crit(self, event):
        """Handle critical hit flash"""
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        
        # Bright yellow flash for crits
        self.add_focus_flash(target_q, target_r, (255, 255, 100), 1.0, 0.25)
        
        # Brief vignette for dramatic effect
        self.set_vignette(0.3, 0.4)
    
    def _on_player_hurt(self, event):
        """Handle player hurt effects"""
        damage = event.get('damage', 0)
        
        # Red color overlay for pain
        overlay_intensity = min(0.4, 0.1 + damage * 0.01)
        self.set_color_overlay((255, 0, 0), overlay_intensity, 0.3)
        
        # Vignette for disorientation
        vignette_intensity = min(0.5, 0.2 + damage * 0.01)
        self.set_vignette(vignette_intensity, 0.6)
    
    def _on_enemy_death(self, event):
        """Handle enemy death effects"""
        q = event.get('q', 0)
        r = event.get('r', 0)
        enemy_type = event.get('enemy_type', '')
        
        if 'boss' in enemy_type.lower():
            # Massive flash for boss death
            self.add_focus_flash(q, r, (255, 200, 100), 1.2, 1.0)
            self.set_vignette(0.8, 2.0)
            self.set_color_overlay((255, 255, 200), 0.3, 1.5)
        else:
            # Regular death flash
            self.add_focus_flash(q, r, (255, 150, 150), 0.6, 0.3)
    
    def _on_floor_change(self, event):
        """Handle floor change effects"""
        # Blue overlay for floor transition
        self.set_color_overlay((100, 150, 255), 0.4, 0.8)
        self.set_vignette(0.6, 1.0)

class CameraManager:
    """Main camera and lighting manager"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.smart_camera = SmartCamera(screen_width, screen_height)
        self.lighting_effects = LightingEffects()
        
        # Current camera state
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
    
    def update(self, dt: float, player_q: int, player_r: int):
        """Update camera and lighting systems"""
        # Always update lighting effects
        self.lighting_effects.update(dt)
        
        if juice_manager.settings.smart_camera_enabled and juice_manager.settings.enabled:
            # Use smart camera system
            self.smart_camera.update(dt, player_q, player_r)
            base_x, base_y = self.smart_camera.get_position()
            self.zoom = self.smart_camera.get_zoom()
        else:
            # Use simple centering
            from .hex_grid import HexGrid
            player_pixel_x, player_pixel_y = HexGrid.hex_to_pixel(player_q, player_r, 0, 0)
            base_x = self.smart_camera.screen_width // 2 - player_pixel_x
            base_y = self.smart_camera.screen_height // 2 - player_pixel_y
            self.zoom = 1.0
        
        # Apply shake from juice manager
        shake_x, shake_y = juice_manager.get_camera_offset()
        
        self.camera_x = int(base_x + shake_x)
        self.camera_y = int(base_y + shake_y)
    
    def get_camera_position(self) -> Tuple[int, int]:
        """Get current camera position"""
        return self.camera_x, self.camera_y
    
    def get_zoom_level(self) -> float:
        """Get current zoom level"""
        return self.zoom
    
    def get_lighting_data(self) -> dict:
        """Get all lighting effect data for rendering"""
        return {
            'focus_flashes': self.lighting_effects.get_focus_flashes(),
            'vignette': self.lighting_effects.get_vignette_data(),
            'color_overlay': self.lighting_effects.get_color_overlay_data()
        }
    
    def focus_on_position(self, q: int, r: int, zoom: float = 1.2):
        """Focus camera on specific position"""
        self.smart_camera.focus_on_position(q, r, zoom)
    
    def center_on_player(self, player_q: int, player_r: int):
        """Center camera on player (for initialization)"""
        if juice_manager.settings.smart_camera_enabled and juice_manager.settings.enabled:
            self.smart_camera._simple_center(player_q, player_r)
            self.camera_x, self.camera_y = self.smart_camera.get_position()
        else:
            # Use simple centering when smart camera is disabled
            from .hex_grid import HexGrid
            player_pixel_x, player_pixel_y = HexGrid.hex_to_pixel(player_q, player_r, 0, 0)
            self.camera_x = self.smart_camera.screen_width // 2 - player_pixel_x
            self.camera_y = self.smart_camera.screen_height // 2 - player_pixel_y

# Global camera manager (will be initialized by game engine)
camera_manager: Optional[CameraManager] = None
