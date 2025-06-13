"""
Visual effects system for enhanced game juice
"""

import time
from typing import Dict, List, Tuple, Optional
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager

class HitFlash:
    """Hit flash effect for entities"""
    
    def __init__(self):
        self.flashes = {}  # entity_id -> flash_data
        
        # Subscribe to events
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
    
    def update(self, dt: float):
        """Update all hit flashes"""
        for entity_id in list(self.flashes.keys()):
            flash_data = self.flashes[entity_id]
            flash_data['timer'] -= dt
            
            if flash_data['timer'] <= 0:
                del self.flashes[entity_id]
    
    def add_flash(self, entity_id: str, flash_type: str = "hit", duration: float = 0.1):
        """Add a hit flash effect"""
        if not juice_manager.settings.enabled:
            return
        
        # Make flashes much more subtle
        duration_multiplier = 0.6  # Shorter duration
        
        self.flashes[entity_id] = {
            'type': flash_type,
            'timer': duration * duration_multiplier,
            'duration': duration * duration_multiplier
        }
    
    def get_flash_color(self, entity_id: str, base_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get modified color for entity if flashing"""
        if entity_id not in self.flashes:
            return base_color
        
        flash_data = self.flashes[entity_id]
        flash_intensity = flash_data['timer'] / flash_data['duration']
        
        # Much more subtle flash effects
        if flash_data['type'] == "hit":
            # Subtle white tint instead of full white
            flash_color = (255, 255, 255)
            max_intensity = 0.3  # Only 30% flash intensity
        elif flash_data['type'] == "critical":
            # Subtle yellow tint for crits
            flash_color = (255, 255, 150)
            max_intensity = 0.4  # 40% for crits
        elif flash_data['type'] == "death":
            # Subtle red tint for death
            flash_color = (255, 150, 150)
            max_intensity = 0.5  # 50% for death
        else:
            flash_color = (255, 255, 255)
            max_intensity = 0.3
        
        # Scale intensity and make it smoother
        actual_intensity = flash_intensity * max_intensity
        
        # Smooth interpolation instead of linear
        smooth_factor = actual_intensity * actual_intensity * (3.0 - 2.0 * actual_intensity)
        
        # Interpolate between base color and flash color
        return tuple(
            int(base_color[i] + (flash_color[i] - base_color[i]) * smooth_factor)
            for i in range(3)
        )
    
    def is_flashing(self, entity_id: str) -> bool:
        """Check if entity is currently flashing"""
        return entity_id in self.flashes
    
    def _on_attack_hit(self, event):
        """Handle attack hit flash"""
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        entity_id = f"enemy_{target_q}_{target_r}"
        
        damage = event.get('damage', 0)
        if damage >= 25:  # High damage
            self.add_flash(entity_id, "critical", 0.08)  # Shorter duration
        else:
            self.add_flash(entity_id, "hit", 0.06)  # Very brief flash
    
    def _on_player_hurt(self, event):
        """Handle player hurt flash"""
        self.add_flash("player", "hit", 0.1)  # Slightly longer for player
    
    def _on_enemy_death(self, event):
        """Handle enemy death flash"""
        q = event.get('q', 0)
        r = event.get('r', 0)
        entity_id = f"enemy_{q}_{r}"
        self.add_flash(entity_id, "death", 0.15)  # Longer for death but still subtle

class MovementTrails:
    """Movement trail effects"""
    
    def __init__(self):
        self.trails = []  # List of trail points
        self.max_trail_length = 8
        
        # Subscribe to movement events
        game_events.subscribe(GameEventType.MOVE_START, self._on_move_start)
        game_events.subscribe(GameEventType.MOVE_END, self._on_move_end)
    
    def update(self, dt: float):
        """Update trail effects"""
        # Fade out trail points
        for trail_point in self.trails[:]:
            trail_point['alpha'] -= dt * 3.0  # Fade over ~0.33 seconds
            if trail_point['alpha'] <= 0:
                self.trails.remove(trail_point)
    
    def add_trail_point(self, x: float, y: float, entity_type: str = "player"):
        """Add a trail point"""
        if not juice_manager.settings.enabled:
            return
        
        self.trails.append({
            'x': x,
            'y': y,
            'entity_type': entity_type,
            'alpha': 1.0,
            'timestamp': time.time()
        })
        
        # Limit trail length
        if len(self.trails) > self.max_trail_length:
            self.trails.pop(0)
    
    def get_trail_points(self) -> List[Dict]:
        """Get current trail points"""
        return self.trails.copy()
    
    def _on_move_start(self, event):
        """Handle movement start"""
        from_q = event.get('from_q', 0)
        from_r = event.get('from_r', 0)
        # Add trail point at starting position
        # This would need hex-to-pixel conversion
        pass
    
    def _on_move_end(self, event):
        """Handle movement end"""
        pass

class VisualEffectsManager:
    """Main manager for all visual effects"""
    
    def __init__(self):
        self.hit_flash = HitFlash()
        self.movement_trails = MovementTrails()
        
        # Screen flash effects
        self.screen_flash_timer = 0.0
        self.screen_flash_color = (255, 255, 255)
        self.screen_flash_alpha = 0.0
        
        # Subscribe to major events for screen flashes
        game_events.subscribe(GameEventType.PLAYER_DEATH, self._on_player_death)
        game_events.subscribe(GameEventType.FLOOR_CHANGE, self._on_floor_change)
    
    def update(self, dt: float):
        """Update all visual effects"""
        self.hit_flash.update(dt)
        self.movement_trails.update(dt)
        
        # Update screen flash
        if self.screen_flash_timer > 0:
            self.screen_flash_timer -= dt
            if self.screen_flash_timer <= 0:
                self.screen_flash_alpha = 0.0
    
    def add_screen_flash(self, color: Tuple[int, int, int], alpha: float, duration: float):
        """Add a screen flash effect"""
        if not juice_manager.settings.enabled:
            return
        
        self.screen_flash_color = color
        self.screen_flash_alpha = alpha * juice_manager.settings.intensity
        self.screen_flash_timer = duration
    
    def get_entity_color(self, entity_id: str, base_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get modified color for entity with all effects applied"""
        color = self.hit_flash.get_flash_color(entity_id, base_color)
        return color
    
    def get_screen_flash_data(self) -> Optional[Dict]:
        """Get current screen flash data"""
        if self.screen_flash_timer > 0:
            return {
                'color': self.screen_flash_color,
                'alpha': self.screen_flash_alpha,
                'timer': self.screen_flash_timer
            }
        return None
    
    def _on_player_death(self, event):
        """Handle player death screen flash"""
        self.add_screen_flash((255, 0, 0), 0.3, 0.5)  # Red flash
    
    def _on_floor_change(self, event):
        """Handle floor change screen flash"""
        self.add_screen_flash((100, 150, 255), 0.2, 0.3)  # Blue flash

# Global visual effects manager
visual_effects = VisualEffectsManager()
