"""
Game juice effects manager with feature flags and frame management
"""

import pygame
import time
import random
from typing import Dict, List, Tuple, Optional
from .game_events import GameEvent, GameEventType, game_events
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

class JuiceSettings:
    """Global settings for juice effects with feature flags"""
    
    def __init__(self):
        # Master juice control
        self.enabled = True
        self.intensity = 1.0  # 0.0 = off, 1.0 = full intensity
        
        # Phase 1: Visual Impact
        self.hit_stop_enabled = True
        self.screen_shake_enabled = True
        self.smooth_movement_enabled = True
        self.exaggerated_animation_enabled = True
        
        # Phase 2: Particles & Overlays
        self.particles_enabled = True
        self.floating_text_enabled = True
        
        # Phase 3: Audio
        self.audio_enabled = True
        self.audio_volume = 0.7
        
        # Phase 4: Camera & Lighting
        self.smart_camera_enabled = True
        self.focus_flash_enabled = True
        self.slow_motion_enabled = True
        
        # Debug
        self.debug_overlay_enabled = False

class FrameClock:
    """Fixed timestep frame clock with pause/slow-motion support"""
    
    def __init__(self, target_fps: int = 60):
        self.target_fps = target_fps
        self.target_dt = 1.0 / target_fps
        self.clock = pygame.time.Clock()
        
        # Pause system
        self.pause_time_remaining = 0.0
        self.is_paused = False
        
        # Slow motion
        self.time_scale = 1.0
        self.slow_motion_timer = 0.0
        
        # Frame tracking
        self.frame_count = 0
        self.actual_fps = 60.0
        self.fps_samples = []
        self.fps_sample_size = 30
    
    def tick(self) -> float:
        """Tick the clock and return delta time"""
        # Get raw delta time
        raw_dt = self.clock.tick(self.target_fps) / 1000.0
        
        # Update FPS tracking
        self.frame_count += 1
        self.fps_samples.append(1.0 / max(raw_dt, 0.001))
        if len(self.fps_samples) > self.fps_sample_size:
            self.fps_samples.pop(0)
        self.actual_fps = sum(self.fps_samples) / len(self.fps_samples)
        
        # Handle pause
        if self.pause_time_remaining > 0:
            self.pause_time_remaining -= raw_dt
            if self.pause_time_remaining <= 0:
                self.is_paused = False
            return 0.0  # No game time passes during pause
        
        # Handle slow motion
        if self.slow_motion_timer > 0:
            self.slow_motion_timer -= raw_dt
            if self.slow_motion_timer <= 0:
                self.time_scale = 1.0
        
        # Return scaled delta time
        return raw_dt * self.time_scale
    
    def pause(self, duration: float):
        """Pause the game for a specific duration (hit-stop effect)"""
        self.pause_time_remaining = duration
        self.is_paused = True
    
    def set_slow_motion(self, scale: float, duration: float):
        """Set slow motion for a duration"""
        self.time_scale = scale
        self.slow_motion_timer = duration
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.actual_fps

class PauseManager:
    """Enhanced pause manager with sophisticated hit-stop effects"""
    
    def __init__(self, frame_clock: FrameClock, settings: JuiceSettings):
        self.frame_clock = frame_clock
        self.settings = settings
        
        # Pause stacking system
        self.pause_queue = []
        self.current_pause = None
        
        # Subscribe to events
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ATTACK_CRIT, self._on_attack_crit)
        game_events.subscribe(GameEventType.SPELL_CAST, self._on_spell_cast)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.GOLD_PICKUP, self._on_gold_pickup)
    
    def add_pause(self, duration: float, priority: int = 1):
        """Add a pause with priority system"""
        if not self.settings.hit_stop_enabled or not self.settings.enabled:
            return
        
        scaled_duration = duration * self.settings.intensity
        
        pause_data = {
            'duration': scaled_duration,
            'priority': priority,
            'timestamp': time.time()
        }
        
        # If no current pause or this has higher priority, use immediately
        if not self.current_pause or priority > self.current_pause['priority']:
            if self.current_pause:
                self.pause_queue.append(self.current_pause)
            self.current_pause = pause_data
            self.frame_clock.pause(scaled_duration)
        else:
            # Queue for later
            self.pause_queue.append(pause_data)
            self.pause_queue.sort(key=lambda x: x['priority'], reverse=True)
    
    def _on_attack_hit(self, event: GameEvent):
        """Handle attack hit pause with damage scaling"""
        damage = event.get('damage', 0)
        enemy_type = event.get('enemy_type', '')
        
        # Base pause duration
        base_pause = 0.06  # 60ms base
        
        # Scale with damage
        damage_multiplier = 1.0 + min(damage / 20.0, 1.5)  # Up to 2.5x for high damage
        
        # Enemy type modifiers
        enemy_modifier = 1.0
        if 'troll' in enemy_type.lower():
            enemy_modifier = 1.3  # Heavier enemies = more impact
        elif 'skeleton' in enemy_type.lower():
            enemy_modifier = 0.8  # Lighter enemies = less impact
        
        pause_duration = base_pause * damage_multiplier * enemy_modifier
        self.add_pause(pause_duration, priority=2)
    
    def _on_attack_crit(self, event: GameEvent):
        """Handle critical hit pause - highest priority"""
        damage = event.get('damage', 0)
        base_pause = 0.18  # 180ms for crits
        damage_bonus = min(damage * 0.005, 0.08)  # Up to 80ms bonus
        
        self.add_pause(base_pause + damage_bonus, priority=5)
    
    def _on_spell_cast(self, event: GameEvent):
        """Handle spell cast pause"""
        spell_power = event.get('power', 1)
        spell_type = event.get('spell_type', 'basic')
        
        base_pause = 0.08  # 80ms base
        
        if spell_type == 'ultimate':
            base_pause = 0.15
        elif spell_type == 'special':
            base_pause = 0.12
        
        self.add_pause(base_pause * spell_power, priority=3)
    
    def _on_enemy_death(self, event: GameEvent):
        """Handle enemy death pause"""
        enemy_type = event.get('enemy_type', '')
        
        if 'boss' in enemy_type.lower():
            # Boss death gets slow motion instead of pause
            self.frame_clock.set_slow_motion(0.2, 1.5)  # 20% speed for 1.5 seconds
        elif 'troll' in enemy_type.lower():
            self.add_pause(0.15, priority=4)  # 150ms for big enemies
        else:
            self.add_pause(0.08, priority=2)  # 80ms for regular enemies
    
    def _on_player_hurt(self, event: GameEvent):
        """Handle player hurt pause - brief but impactful"""
        damage = event.get('damage', 0)
        
        # Player hurt gets shorter pause but higher priority
        base_pause = 0.04  # 40ms base
        damage_bonus = min(damage * 0.002, 0.04)  # Up to 40ms bonus
        
        self.add_pause(base_pause + damage_bonus, priority=4)
    
    def _on_gold_pickup(self, event: GameEvent):
        """Handle gold pickup - very brief positive pause"""
        amount = event.get('amount', 0)
        
        if amount >= 100:  # Large gold pickup
            self.add_pause(0.03, priority=1)  # 30ms pause for satisfaction

class ScreenShake:
    """Enhanced screen shake effect manager with multiple shake types"""
    
    def __init__(self, settings: JuiceSettings):
        self.settings = settings
        self.shake_offset = [0, 0]
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_frequency = 30.0  # Shakes per second
        self.shake_type = "random"  # "random", "horizontal", "vertical", "circular"
        
        # Multiple shake layers
        self.shake_layers = []
        
        # Subscribe to events
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.SPELL_CAST, self._on_spell_cast)
        game_events.subscribe(GameEventType.GOLD_PICKUP, self._on_gold_pickup)
    
    def update(self, dt: float):
        """Update shake effect with multiple layers"""
        total_offset = [0, 0]
        
        # Update all shake layers
        for shake_layer in self.shake_layers[:]:
            shake_layer['timer'] -= dt
            
            if shake_layer['timer'] <= 0:
                self.shake_layers.remove(shake_layer)
                continue
            
            # Calculate shake intensity with falloff
            intensity_factor = shake_layer['timer'] / shake_layer['duration']
            current_intensity = shake_layer['intensity'] * intensity_factor
            
            # Generate shake offset based on type
            if shake_layer['type'] == "random":
                offset = self._generate_random_shake(current_intensity, dt)
            elif shake_layer['type'] == "horizontal":
                offset = self._generate_horizontal_shake(current_intensity, dt)
            elif shake_layer['type'] == "vertical":
                offset = self._generate_vertical_shake(current_intensity, dt)
            elif shake_layer['type'] == "circular":
                offset = self._generate_circular_shake(current_intensity, dt, shake_layer['timer'])
            else:
                offset = [0, 0]
            
            total_offset[0] += offset[0]
            total_offset[1] += offset[1]
        
        # Apply intensity scaling
        self.shake_offset[0] = int(total_offset[0] * self.settings.intensity)
        self.shake_offset[1] = int(total_offset[1] * self.settings.intensity)
        
        # Legacy single shake system (for backward compatibility)
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_offset = [0, 0]
                self.shake_intensity = 0.0
            else:
                intensity = self.shake_intensity * (self.shake_timer / 0.3)
                legacy_offset = self._generate_random_shake(intensity, dt)
                self.shake_offset[0] += int(legacy_offset[0])
                self.shake_offset[1] += int(legacy_offset[1])
    
    def _generate_random_shake(self, intensity: float, dt: float) -> list:
        """Generate random shake offset"""
        import random
        return [
            random.uniform(-intensity, intensity),
            random.uniform(-intensity, intensity)
        ]
    
    def _generate_horizontal_shake(self, intensity: float, dt: float) -> list:
        """Generate horizontal-only shake"""
        import random
        return [random.uniform(-intensity, intensity), 0]
    
    def _generate_vertical_shake(self, intensity: float, dt: float) -> list:
        """Generate vertical-only shake"""
        import random
        return [0, random.uniform(-intensity, intensity)]
    
    def _generate_circular_shake(self, intensity: float, dt: float, timer: float) -> list:
        """Generate circular shake pattern"""
        import math
        angle = timer * self.shake_frequency * 2 * math.pi
        return [
            math.cos(angle) * intensity,
            math.sin(angle) * intensity
        ]
    
    def add_shake_layer(self, intensity: float, duration: float = 0.3, shake_type: str = "random"):
        """Add a new shake layer"""
        if not self.settings.screen_shake_enabled or not self.settings.enabled:
            return
        
        self.shake_layers.append({
            'intensity': intensity,
            'duration': duration,
            'timer': duration,
            'type': shake_type
        })
    
    def add_shake(self, intensity: float, duration: float = 0.3):
        """Add screen shake effect (legacy method)"""
        if not self.settings.screen_shake_enabled or not self.settings.enabled:
            return
        
        self.shake_intensity = max(self.shake_intensity, intensity * self.settings.intensity)
        self.shake_timer = max(self.shake_timer, duration)
    
    def get_offset(self) -> Tuple[int, int]:
        """Get current shake offset"""
        return tuple(self.shake_offset)
    
    def _on_attack_hit(self, event: GameEvent):
        """Handle attack hit shake with directional effect"""
        damage = event.get('damage', 0)
        base_shake = 3.0
        damage_bonus = min(damage * 0.3, 10.0)
        
        # Add main impact shake
        self.add_shake_layer(base_shake + damage_bonus, 0.15, "random")
        
        # Add subtle horizontal shake for impact feel
        self.add_shake_layer((base_shake + damage_bonus) * 0.5, 0.25, "horizontal")
    
    def _on_player_hurt(self, event: GameEvent):
        """Handle player hurt shake - more intense and longer"""
        damage = event.get('damage', 0)
        shake_intensity = min(8.0 + damage * 0.4, 20.0)
        
        # Strong random shake for pain
        self.add_shake_layer(shake_intensity, 0.4, "random")
        
        # Circular shake for disorientation
        self.add_shake_layer(shake_intensity * 0.3, 0.6, "circular")
    
    def _on_enemy_death(self, event: GameEvent):
        """Handle enemy death shake"""
        enemy_type = event.get('enemy_type', '')
        
        if 'boss' in enemy_type.lower():
            # Massive shake for boss death
            self.add_shake_layer(25.0, 0.8, "circular")
            self.add_shake_layer(15.0, 1.2, "random")
        elif 'troll' in enemy_type.lower():
            # Heavy shake for large enemies
            self.add_shake_layer(12.0, 0.4, "vertical")
            self.add_shake_layer(8.0, 0.6, "random")
        else:
            # Standard enemy death
            self.add_shake_layer(6.0, 0.25, "random")
    
    def _on_spell_cast(self, event: GameEvent):
        """Handle spell cast shake"""
        spell_power = event.get('power', 1)
        self.add_shake_layer(4.0 * spell_power, 0.2, "circular")
    
    def _on_gold_pickup(self, event: GameEvent):
        """Handle gold pickup - subtle positive shake"""
        amount = event.get('amount', 0)
        if amount >= 50:  # Large gold pickup
            self.add_shake_layer(2.0, 0.15, "vertical")

class JuiceManager:
    """Main manager for all juice effects"""
    
    def __init__(self):
        self.settings = JuiceSettings()
        self.frame_clock = FrameClock()
        self.pause_manager = PauseManager(self.frame_clock, self.settings)
        self.screen_shake = ScreenShake(self.settings)
        
        # Debug info
        self.debug_info = {
            'fps': 0.0,
            'particles': 0,
            'active_shakes': 0,
            'paused_frames': 0
        }
    
    def update(self, dt: float):
        """Update all juice effects"""
        self.screen_shake.update(dt)
        
        # Update debug info
        self.debug_info['fps'] = self.frame_clock.get_fps()
        self.debug_info['active_shakes'] = len(self.screen_shake.shake_layers)
        self.debug_info['paused_frames'] = 1 if self.frame_clock.is_paused else 0
        
        # Update particle count (will be set by particle system)
        from .particle_system import particle_system
        self.debug_info['particles'] = particle_system.get_particle_count()
    
    def tick(self) -> float:
        """Tick the frame clock"""
        return self.frame_clock.tick()
    
    def get_camera_offset(self) -> Tuple[int, int]:
        """Get camera offset including shake"""
        return self.screen_shake.get_offset()
    
    def toggle_debug(self):
        """Toggle debug overlay"""
        self.settings.debug_overlay_enabled = not self.settings.debug_overlay_enabled
    
    def set_intensity(self, intensity: float):
        """Set master juice intensity (0.0 to 1.0)"""
        self.settings.intensity = max(0.0, min(1.0, intensity))
    
    def toggle_juice(self):
        """Toggle all juice effects"""
        self.settings.enabled = not self.settings.enabled

# Global juice manager instance
juice_manager = JuiceManager()
