"""
ASCII Particle System for enhanced visual effects
"""

import random
import math
import time
from typing import List, Dict, Tuple, Optional
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager
from .hex_grid import HexGrid

class FXParticle:
    """Individual ASCII particle"""
    
    def __init__(self, x: float, y: float, glyph: str, color: Tuple[int, int, int], 
                 velocity: Tuple[float, float], ttl: float, gravity: float = 0.0,
                 fade_type: str = "linear"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.glyph = glyph
        self.color = color
        self.base_color = color
        self.velocity_x, self.velocity_y = velocity
        self.ttl = ttl
        self.max_ttl = ttl
        self.gravity = gravity
        self.fade_type = fade_type
        self.scale = 1.0
        self.rotation = 0.0
        self.angular_velocity = 0.0
        
        # Physics
        self.friction = 0.98
        self.bounce = 0.3
        self.ground_y = None  # Ground collision
        
        # Animation
        self.pulse_speed = 0.0
        self.pulse_amplitude = 0.0
    
    def update(self, dt: float) -> bool:
        """Update particle. Returns False if particle should be removed."""
        # Update lifetime
        self.ttl -= dt
        if self.ttl <= 0:
            return False
        
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Apply gravity
        if self.gravity != 0:
            self.velocity_y += self.gravity * dt
        
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        # Ground collision
        if self.ground_y is not None and self.y >= self.ground_y:
            self.y = self.ground_y
            self.velocity_y *= -self.bounce
            if abs(self.velocity_y) < 10:  # Stop bouncing when slow
                self.velocity_y = 0
        
        # Update rotation
        self.rotation += self.angular_velocity * dt
        
        # Update color based on fade type
        life_progress = 1.0 - (self.ttl / self.max_ttl)
        
        if self.fade_type == "linear":
            alpha = self.ttl / self.max_ttl
        elif self.fade_type == "ease_out":
            alpha = math.pow(self.ttl / self.max_ttl, 0.5)
        elif self.fade_type == "flash":
            # Flash bright then fade
            if life_progress < 0.2:
                alpha = 1.0
            else:
                alpha = (self.ttl / self.max_ttl) * 0.8
        else:
            alpha = self.ttl / self.max_ttl
        
        # Apply pulse effect
        if self.pulse_speed > 0:
            pulse = math.sin(time.time() * self.pulse_speed) * self.pulse_amplitude
            alpha += pulse
        
        alpha = max(0.0, min(1.0, alpha))
        
        # Update color with alpha
        self.color = tuple(int(c * alpha) for c in self.base_color)
        
        return True
    
    def get_render_data(self) -> Dict:
        """Get data for rendering"""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'glyph': self.glyph,
            'color': self.color,
            'scale': self.scale,
            'rotation': self.rotation
        }

class ParticleSpawner:
    """Spawns different types of particle effects"""
    
    @staticmethod
    def spawn_sparks(x: float, y: float, count: int = 8, color: Tuple[int, int, int] = (255, 255, 100)) -> List[FXParticle]:
        """Spawn spark particles for hits"""
        particles = []
        
        spark_glyphs = ['*', '+', '·', '°', '˚']
        
        for _ in range(count):
            # Random direction
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            
            velocity = (
                math.cos(angle) * speed,
                math.sin(angle) * speed
            )
            
            glyph = random.choice(spark_glyphs)
            ttl = random.uniform(0.3, 0.8)
            
            # Add some position variance
            spawn_x = x + random.uniform(-5, 5)
            spawn_y = y + random.uniform(-5, 5)
            
            particle = FXParticle(spawn_x, spawn_y, glyph, color, velocity, ttl, 
                                gravity=50, fade_type="flash")
            particle.angular_velocity = random.uniform(-10, 10)
            
            particles.append(particle)
        
        return particles
    
    @staticmethod
    def spawn_debris(x: float, y: float, count: int = 6, debris_type: str = "stone") -> List[FXParticle]:
        """Spawn debris particles for destruction"""
        particles = []
        
        if debris_type == "stone":
            debris_glyphs = ['▪', '▫', '■', '□', '▴', '▾']
            color = (150, 150, 150)
        elif debris_type == "wood":
            debris_glyphs = ['/', '\\', '|', '-', '╱', '╲']
            color = (139, 69, 19)
        elif debris_type == "bone":
            debris_glyphs = ['⌐', '¬', '┐', '└', '┘', '┌']
            color = (220, 220, 200)
        else:
            debris_glyphs = ['*', '+', 'x', '○', '●']
            color = (200, 200, 200)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 60)
            
            velocity = (
                math.cos(angle) * speed,
                math.sin(angle) * speed - 20  # Slight upward bias
            )
            
            glyph = random.choice(debris_glyphs)
            ttl = random.uniform(0.8, 1.5)
            
            spawn_x = x + random.uniform(-8, 8)
            spawn_y = y + random.uniform(-8, 8)
            
            particle = FXParticle(spawn_x, spawn_y, glyph, color, velocity, ttl,
                                gravity=80, fade_type="linear")
            particle.ground_y = y + 30  # Set ground level
            particle.angular_velocity = random.uniform(-5, 5)
            
            particles.append(particle)
        
        return particles
    
    @staticmethod
    def spawn_splash(x: float, y: float, count: int = 10, liquid_type: str = "water") -> List[FXParticle]:
        """Spawn splash particles for liquid effects"""
        particles = []
        
        if liquid_type == "water":
            splash_glyphs = ['~', '≈', '∼', '◦', '°']
            color = (100, 150, 255)
        elif liquid_type == "blood":
            splash_glyphs = ['•', '·', '°', '˚', '∘']
            color = (200, 50, 50)
        elif liquid_type == "acid":
            splash_glyphs = ['~', '≈', '∼', '◦', '°']
            color = (150, 255, 100)
        else:
            splash_glyphs = ['~', '≈', '∼']
            color = (150, 150, 255)
        
        for _ in range(count):
            # Splash pattern - more horizontal spread
            angle = random.uniform(-math.pi/3, math.pi/3) + math.pi/2  # Upward arc
            speed = random.uniform(40, 100)
            
            velocity = (
                math.cos(angle) * speed,
                math.sin(angle) * speed
            )
            
            glyph = random.choice(splash_glyphs)
            ttl = random.uniform(0.4, 1.0)
            
            spawn_x = x + random.uniform(-3, 3)
            spawn_y = y + random.uniform(-3, 3)
            
            particle = FXParticle(spawn_x, spawn_y, glyph, color, velocity, ttl,
                                gravity=120, fade_type="ease_out")
            particle.ground_y = y + 25
            
            particles.append(particle)
        
        return particles
    
    @staticmethod
    def spawn_magic_burst(x: float, y: float, count: int = 12, magic_type: str = "arcane") -> List[FXParticle]:
        """Spawn magical effect particles"""
        particles = []
        
        if magic_type == "arcane":
            magic_glyphs = ['✦', '✧', '✩', '✪', '✫', '✬', '✭', '✮', '✯', '✰']
            color = (150, 100, 255)
        elif magic_type == "fire":
            magic_glyphs = ['▲', '▴', '▵', '△', '◆', '◇', '◈']
            color = (255, 100, 50)
        elif magic_type == "ice":
            magic_glyphs = ['❅', '❆', '❇', '❈', '❉', '❊', '❋']
            color = (150, 200, 255)
        elif magic_type == "nature":
            magic_glyphs = ['❀', '❁', '❂', '❃', '❄', '❅', '❆']
            color = (100, 255, 100)
        else:
            magic_glyphs = ['*', '✦', '✧', '✩']
            color = (255, 255, 100)
        
        for _ in range(count):
            # Circular burst pattern
            angle = (2 * math.pi * _) / count + random.uniform(-0.2, 0.2)
            speed = random.uniform(30, 70)
            
            velocity = (
                math.cos(angle) * speed,
                math.sin(angle) * speed
            )
            
            glyph = random.choice(magic_glyphs)
            ttl = random.uniform(0.6, 1.2)
            
            particle = FXParticle(x, y, glyph, color, velocity, ttl,
                                gravity=0, fade_type="flash")
            particle.pulse_speed = 8.0
            particle.pulse_amplitude = 0.3
            
            particles.append(particle)
        
        return particles

class FXText:
    """Enhanced floating text with more effects"""
    
    def __init__(self, x: float, y: float, text: str, color: Tuple[int, int, int],
                 ttl: float, font_size: str = "normal", animation_type: str = "float"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.text = text
        self.color = color
        self.base_color = color
        self.ttl = ttl
        self.max_ttl = ttl
        self.font_size = font_size
        self.animation_type = animation_type
        
        # Animation properties
        self.velocity_x = 0.0
        self.velocity_y = -30.0  # Default upward movement
        self.scale = 1.0
        self.rotation = 0.0
        
        # Set animation based on type
        if animation_type == "damage":
            self.velocity_y = -50.0
            self.scale = 1.2
        elif animation_type == "critical":
            self.velocity_y = -40.0
            self.scale = 1.5
            self.rotation = random.uniform(-5, 5)
        elif animation_type == "gold":
            self.velocity_y = -25.0
            self.velocity_x = random.uniform(-10, 10)
        elif animation_type == "popup":
            self.velocity_y = 0.0
            self.scale = 0.5  # Start small, grow
    
    def update(self, dt: float) -> bool:
        """Update floating text. Returns False if should be removed."""
        self.ttl -= dt
        if self.ttl <= 0:
            return False
        
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Animation-specific updates
        life_progress = 1.0 - (self.ttl / self.max_ttl)
        
        if self.animation_type == "damage":
            # Quick upward movement with bounce
            if life_progress < 0.3:
                self.y = self.start_y - (life_progress * 60)
            else:
                self.y = self.start_y - 18 - ((life_progress - 0.3) * 20)
        
        elif self.animation_type == "critical":
            # Larger movement with shake
            shake_x = math.sin(life_progress * 20) * 2
            self.x = self.start_x + shake_x
            
        elif self.animation_type == "popup":
            # Scale up then fade
            if life_progress < 0.2:
                self.scale = 0.5 + (life_progress * 2.5)  # Scale from 0.5 to 1.0
            else:
                self.scale = 1.0
        
        # Update alpha
        alpha = self.ttl / self.max_ttl
        if self.animation_type == "critical":
            # Flash effect for crits
            flash = math.sin(life_progress * 15) * 0.2 + 0.8
            alpha *= flash
        
        alpha = max(0.0, min(1.0, alpha))
        self.color = tuple(int(c * alpha) for c in self.base_color)
        
        return True
    
    def get_render_data(self) -> Dict:
        """Get data for rendering"""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'text': self.text,
            'color': self.color,
            'font_size': self.font_size,
            'scale': self.scale,
            'rotation': self.rotation
        }

class ParticleSystem:
    """Main particle system manager"""
    
    def __init__(self):
        self.particles: List[FXParticle] = []
        self.text_effects: List[FXText] = []
        self.max_particles = 200
        self.max_text_effects = 50
        
        # Subscribe to events
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ATTACK_CRIT, self._on_attack_crit)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.GOLD_PICKUP, self._on_gold_pickup)
        game_events.subscribe(GameEventType.SPELL_CAST, self._on_spell_cast)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
    
    def update(self, dt: float):
        """Update all particles and text effects"""
        if not juice_manager.settings.particles_enabled or not juice_manager.settings.enabled:
            return
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Update text effects
        self.text_effects = [t for t in self.text_effects if t.update(dt)]
    
    def add_particles(self, particles: List[FXParticle]):
        """Add particles to the system"""
        if not juice_manager.settings.particles_enabled or not juice_manager.settings.enabled:
            return
        
        # Scale particle count by intensity
        count_multiplier = juice_manager.settings.intensity
        particles = particles[:int(len(particles) * count_multiplier)]
        
        self.particles.extend(particles)
        
        # Limit total particles
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def add_text_effect(self, text_effect: FXText):
        """Add text effect to the system"""
        if not juice_manager.settings.floating_text_enabled or not juice_manager.settings.enabled:
            return
        
        self.text_effects.append(text_effect)
        
        # Limit total text effects
        if len(self.text_effects) > self.max_text_effects:
            self.text_effects.pop(0)
    
    def get_particle_count(self) -> int:
        """Get current particle count"""
        return len(self.particles)
    
    def get_text_effect_count(self) -> int:
        """Get current text effect count"""
        return len(self.text_effects)
    
    def get_particles_for_render(self) -> List[Dict]:
        """Get particle render data"""
        return [p.get_render_data() for p in self.particles]
    
    def get_text_effects_for_render(self) -> List[Dict]:
        """Get text effect render data"""
        return [t.get_render_data() for t in self.text_effects]
    
    def clear_all(self):
        """Clear all particles and effects"""
        self.particles.clear()
        self.text_effects.clear()
    
    def _on_attack_hit(self, event):
        """Handle attack hit particles"""
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        damage = event.get('damage', 0)
        enemy_type = event.get('enemy_type', '')
        
        # Get screen position with camera offset
        x, y = self._get_screen_position(target_q, target_r)
        
        # Spawn sparks
        spark_count = min(3 + damage // 5, 12)
        sparks = ParticleSpawner.spawn_sparks(x, y, spark_count)
        self.add_particles(sparks)
        
        # Spawn debris based on enemy type
        if 'skeleton' in enemy_type:
            debris = ParticleSpawner.spawn_debris(x, y, 4, "bone")
            self.add_particles(debris)
        elif 'troll' in enemy_type:
            debris = ParticleSpawner.spawn_debris(x, y, 6, "stone")
            self.add_particles(debris)
    
    def _on_attack_crit(self, event):
        """Handle critical hit particles"""
        target_q = event.get('target_q', 0)
        target_r = event.get('target_r', 0)
        
        x, y = self._get_screen_position(target_q, target_r)
        
        # Bright sparks
        sparks = ParticleSpawner.spawn_sparks(x, y, 15, (255, 255, 150))
        self.add_particles(sparks)
        
        # Magic burst for visual impact
        magic = ParticleSpawner.spawn_magic_burst(x, y, 8, "arcane")
        self.add_particles(magic)
    
    def _on_enemy_death(self, event):
        """Handle enemy death particles"""
        q = event.get('q', 0)
        r = event.get('r', 0)
        enemy_type = event.get('enemy_type', '')
        
        x, y = self._get_screen_position(q, r)
        
        # Death explosion
        if 'boss' in enemy_type.lower():
            # Massive explosion for bosses
            sparks = ParticleSpawner.spawn_sparks(x, y, 25, (255, 100, 100))
            magic = ParticleSpawner.spawn_magic_burst(x, y, 20, "fire")
            debris = ParticleSpawner.spawn_debris(x, y, 15, "stone")
            self.add_particles(magic)
        else:
            # Regular death effects
            sparks = ParticleSpawner.spawn_sparks(x, y, 8, (200, 100, 100))
            if 'skeleton' in enemy_type:
                debris = ParticleSpawner.spawn_debris(x, y, 6, "bone")
            else:
                debris = ParticleSpawner.spawn_debris(x, y, 4, "stone")
            self.add_particles(debris)
        
        self.add_particles(sparks)
    
    def _on_gold_pickup(self, event):
        """Handle gold pickup particles"""
        q = event.get('q', 0)
        r = event.get('r', 0)
        amount = event.get('amount', 0)
        
        x, y = self._get_screen_position(q, r)
        
        # Golden sparkles
        sparkle_count = min(3 + amount // 10, 10)
        sparkles = ParticleSpawner.spawn_sparks(x, y, sparkle_count, (255, 215, 0))
        self.add_particles(sparkles)
    
    def _on_player_hurt(self, event):
        """Handle player hurt particles"""
        damage = event.get('damage', 0)
        player_q = event.get('player_q', 0)
        player_r = event.get('player_r', 0)
        
        # Get player screen position
        x, y = self._get_screen_position(player_q, player_r)
        
        # Blood splash effect
        splash = ParticleSpawner.spawn_splash(x, y, min(5 + damage // 3, 12), "blood")
        self.add_particles(splash)
    
    def _on_spell_cast(self, event):
        """Handle spell cast particles"""
        spell_type = event.get('spell_type', 'arcane')
        power = event.get('power', 1)
        caster_q = event.get('caster_q', 0)
        caster_r = event.get('caster_r', 0)
        
        # Get caster position (usually player)
        x, y = self._get_screen_position(caster_q, caster_r)
        
        magic = ParticleSpawner.spawn_magic_burst(x, y, 6 * power, spell_type)
        self.add_particles(magic)
    
    def _get_screen_position(self, q: int, r: int) -> Tuple[float, float]:
        """Convert hex coordinates to screen position with camera offset"""
        # Get world position
        world_x, world_y = HexGrid.hex_to_pixel(q, r, 0, 0)
        
        # Apply camera offset
        from .camera_system import camera_manager
        if camera_manager:
            camera_x, camera_y = camera_manager.get_camera_position()
            screen_x = world_x + camera_x
            screen_y = world_y + camera_y
        else:
            # Fallback if no camera manager
            screen_x, screen_y = world_x, world_y
        
        return float(screen_x), float(screen_y)
    
    def _get_player_screen_position(self) -> Tuple[float, float]:
        """Get player's current screen position"""
        # This is a bit tricky since we don't have direct access to the player
        # We'll need to get this from the game engine or use a different approach
        from .camera_system import camera_manager
        if camera_manager:
            # Assume player is at screen center when camera is following
            screen_width = camera_manager.smart_camera.screen_width
            screen_height = camera_manager.smart_camera.screen_height
            return float(screen_width // 2), float(screen_height // 2)
        else:
            # Fallback
            return 400.0, 300.0

# Global particle system instance
particle_system = ParticleSystem()
