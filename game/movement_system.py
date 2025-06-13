"""
Enhanced movement system with easing and anticipation
"""

import math
from typing import Tuple, Optional
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager

class EasingFunctions:
    """Collection of easing functions for smooth animations"""
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Ease-out cubic: fast start, slow end"""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Ease-in cubic: slow start, fast end"""
        return t * t * t
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Ease-in-out cubic: slow start and end, fast middle"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """Ease-out back: overshoot and settle"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Ease-out bounce: bouncy landing"""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

class SmoothMovement:
    """Enhanced movement with easing and anticipation"""
    
    def __init__(self):
        self.is_moving = False
        self.move_timer = 0.0
        self.move_duration = 0.4  # Slightly longer for smoother feel
        
        # Movement data
        self.start_pos: Optional[Tuple[float, float]] = None
        self.target_pos: Optional[Tuple[float, float]] = None
        self.current_pos: Optional[Tuple[float, float]] = None
        
        # Anticipation phase
        self.anticipation_duration = 0.08  # 80ms anticipation
        self.anticipation_offset = 8  # pixels to move backward
        
        # Movement direction for anticipation
        self.move_direction: Optional[Tuple[float, float]] = None
        
        # Subscribe to movement events
        game_events.subscribe(GameEventType.MOVE_START, self._on_move_start)
    
    def start_move(self, from_pos: Tuple[float, float], to_pos: Tuple[float, float]):
        """Start a smooth movement with anticipation"""
        if not juice_manager.settings.smooth_movement_enabled or not juice_manager.settings.enabled:
            # Instant movement if juice disabled
            self.current_pos = to_pos
            self.is_moving = False
            return
        
        self.is_moving = True
        self.move_timer = 0.0
        self.start_pos = from_pos
        self.target_pos = to_pos
        self.current_pos = from_pos
        
        # Calculate movement direction for anticipation
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length > 0:
            self.move_direction = (-dx / length, -dy / length)  # Opposite direction
        else:
            self.move_direction = (0, 0)
    
    def update(self, dt: float) -> bool:
        """Update movement animation. Returns True if movement finished."""
        if not self.is_moving:
            return False
        
        self.move_timer += dt
        progress = min(self.move_timer / self.move_duration, 1.0)
        
        if juice_manager.settings.exaggerated_animation_enabled and juice_manager.settings.enabled:
            # Phase 1: Anticipation (move slightly backward)
            if progress < (self.anticipation_duration / self.move_duration):
                anticipation_progress = progress / (self.anticipation_duration / self.move_duration)
                anticipation_amount = EasingFunctions.ease_out_cubic(anticipation_progress)
                
                offset_x = self.move_direction[0] * self.anticipation_offset * anticipation_amount
                offset_y = self.move_direction[1] * self.anticipation_offset * anticipation_amount
                
                self.current_pos = (
                    self.start_pos[0] + offset_x,
                    self.start_pos[1] + offset_y
                )
            
            # Phase 2: Main movement (ease-out for snappy feel)
            else:
                main_progress = (progress - (self.anticipation_duration / self.move_duration)) / (1.0 - (self.anticipation_duration / self.move_duration))
                eased_progress = EasingFunctions.ease_out_back(main_progress)
                
                # Interpolate from start to target
                self.current_pos = (
                    self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * eased_progress,
                    self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * eased_progress
                )
        else:
            # Simple easing without anticipation
            eased_progress = EasingFunctions.ease_out_cubic(progress)
            self.current_pos = (
                self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * eased_progress,
                self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * eased_progress
            )
        
        # Check if movement finished
        if progress >= 1.0:
            self.current_pos = self.target_pos
            self.is_moving = False
            
            # Emit move end event
            game_events.emit(GameEventType.MOVE_END, {
                'final_pos': self.target_pos
            })
            
            return True
        
        return False
    
    def get_current_position(self) -> Tuple[float, float]:
        """Get current interpolated position"""
        return self.current_pos if self.current_pos else (0, 0)
    
    def _on_move_start(self, event):
        """Handle move start event from game"""
        # This will be called by the player when movement starts
        pass

class EnhancedPlayer:
    """Enhanced player with smooth movement"""
    
    def __init__(self, start_q: int, start_r: int):
        self.q = start_q
        self.r = start_r
        self.health = 100
        self.max_health = 100
        self.gold = 0
        self.floor = 1
        
        # Enhanced movement system
        self.smooth_movement = SmoothMovement()
        
        # Legacy compatibility
        self.is_moving = False
        self.move_timer = 0.0
        self.move_duration = 0.3
        self.start_pos = None
        self.target_pos = None
    
    def move_to(self, new_q: int, new_r: int, offset_x: int, offset_y: int):
        """Start moving to a new hex position with smooth animation"""
        from .hex_grid import HexGrid
        
        # Get pixel positions
        start_pixel = HexGrid.hex_to_pixel(self.q, self.r, offset_x, offset_y)
        target_pixel = HexGrid.hex_to_pixel(new_q, new_r, offset_x, offset_y)
        
        # Update hex coordinates immediately (for game logic)
        self.q = new_q
        self.r = new_r
        
        # Start smooth movement animation
        self.smooth_movement.start_move(start_pixel, target_pixel)
        
        # Legacy compatibility
        self.is_moving = True
        self.move_timer = 0.0
        self.start_pos = start_pixel
        self.target_pos = target_pixel
    
    def update(self, dt: float):
        """Update player state"""
        # Update smooth movement
        movement_finished = self.smooth_movement.update(dt)
        
        # Update legacy movement system for compatibility
        if self.is_moving:
            self.move_timer += dt
            if self.move_timer >= self.move_duration or movement_finished:
                self.is_moving = False
                self.move_timer = 0.0
    
    def get_render_position(self, offset_x: int, offset_y: int) -> Tuple[int, int]:
        """Get current render position (smooth interpolated)"""
        if juice_manager.settings.smooth_movement_enabled and juice_manager.settings.enabled and self.smooth_movement.is_moving:
            # Use smooth movement position during animation
            pos = self.smooth_movement.get_current_position()
            return int(pos[0]), int(pos[1])
        else:
            # Use standard hex-to-pixel conversion when not moving
            from .hex_grid import HexGrid
            return HexGrid.hex_to_pixel(self.q, self.r, offset_x, offset_y)
    
    def take_damage(self, damage: int):
        """Take damage"""
        self.health = max(0, self.health - damage)
    
    def collect_gold(self, amount: int):
        """Collect gold"""
        self.gold += amount
    
    def go_to_next_floor(self):
        """Go to next floor and restore some health"""
        self.floor += 1
        # Restore 20% of max health when going to next floor
        health_restore = int(self.max_health * 0.2)
        self.health = min(self.max_health, self.health + health_restore)
