"""
Audio feedback system for enhanced game juice
"""

import pygame
import random
import os
from typing import Dict, List, Optional, Tuple
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager

class AudioManager:
    """Manages all game audio with layering and dynamic effects"""
    
    def __init__(self):
        # Initialize pygame mixer
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error:
            print("Audio system not available, using fallback")
            self.audio_available = False
        
        # Audio channels for layering
        self.max_channels = 8
        if self.audio_available:
            pygame.mixer.set_num_channels(self.max_channels)
        
        # Sound libraries
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.sound_variations: Dict[str, List[pygame.mixer.Sound]] = {}
        
        # Volume settings
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.ambient_volume = 0.3
        
        # Audio state
        self.muted = False
        self.current_ambient = None
        
        # Generate procedural sounds
        self._generate_procedural_sounds()
        
        # Subscribe to events
        self._subscribe_to_events()
    
    def _generate_procedural_sounds(self):
        """Generate simple procedural sounds using pygame"""
        if not self.audio_available:
            return
        
    def _generate_procedural_sounds(self):
        """Generate simple procedural sounds using pygame"""
        if not self.audio_available:
            return
        
        try:
            # Try to use numpy for better sound generation
            import numpy as np
            self._generate_numpy_sounds()
        except ImportError:
            # Fallback to simple pygame sound generation
            self._generate_simple_sounds()
        except Exception as e:
            print(f"Could not generate procedural sounds: {e}")
            self.audio_available = False
    
    def _generate_simple_sounds(self):
        """Generate simple sounds without numpy"""
        import array
        import math
        
        sample_rate = 22050
        
        # Generate simple sine wave sounds
        def generate_tone(frequency: float, duration: float, volume: float = 0.3):
            frames = int(duration * sample_rate)
            arr = array.array('h')
            
            for i in range(frames):
                time_point = float(i) / sample_rate
                # Simple sine wave with decay
                wave_value = int(volume * 32767 * 
                               math.sin(2 * math.pi * frequency * time_point) *
                               math.exp(-time_point * 3))  # Decay envelope
                arr.append(wave_value)
                arr.append(wave_value)  # Stereo
            
            return pygame.sndarray.make_sound(arr)
        
        # Generate basic sounds
        self.sounds['hit_light'] = generate_tone(800, 0.1, 0.3)
        self.sounds['hit_heavy'] = generate_tone(400, 0.15, 0.4)
        self.sounds['hit_crit'] = generate_tone(1200, 0.12, 0.35)
        self.sounds['ui_select'] = generate_tone(600, 0.08, 0.2)
        self.sounds['gold_pickup'] = generate_tone(1000, 0.3, 0.25)
        self.sounds['spell_cast'] = generate_tone(600, 0.4, 0.3)
        self.sounds['ambient_dungeon'] = generate_tone(60, 2.0, 0.1)
    
    def _generate_numpy_sounds(self):
        """Generate enhanced sounds with numpy"""
        sample_rate = 22050
        
        # Hit sounds - short percussive
        self._generate_hit_sounds(sample_rate)
        
        # UI sounds - clean tones
        self._generate_ui_sounds(sample_rate)
        
        # Ambient sounds - longer tones
        self._generate_ambient_sounds(sample_rate)
        
        # Magic sounds - ethereal tones
        self._generate_magic_sounds(sample_rate)
    
    def _generate_hit_sounds(self, sample_rate: int):
        """Generate hit/impact sounds"""
        import numpy as np
        
        # Light hit
        duration = 0.1
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Sharp attack, quick decay
        frequency = 800
        wave = np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t * 15)  # Quick decay
        audio = (wave * envelope * 0.3 * 32767).astype(np.int16)
        
        # Convert to stereo
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['hit_light'] = pygame.sndarray.make_sound(stereo_audio)
        
        # Heavy hit - lower frequency, longer
        frequency = 400
        duration = 0.15
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        wave = np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t * 8)
        audio = (wave * envelope * 0.4 * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['hit_heavy'] = pygame.sndarray.make_sound(stereo_audio)
        
        # Critical hit - bright, sharp
        frequency = 1200
        duration = 0.12
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Add harmonics for brightness
        wave = (np.sin(2 * np.pi * frequency * t) + 
                0.5 * np.sin(2 * np.pi * frequency * 2 * t) +
                0.25 * np.sin(2 * np.pi * frequency * 3 * t))
        envelope = np.exp(-t * 12)
        audio = (wave * envelope * 0.35 * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['hit_crit'] = pygame.sndarray.make_sound(stereo_audio)
    
    def _generate_ui_sounds(self, sample_rate: int):
        """Generate UI interaction sounds"""
        import numpy as np
        
        # Menu select - pleasant tone
        duration = 0.08
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        frequency = 600
        wave = np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t * 8)
        audio = (wave * envelope * 0.2 * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['ui_select'] = pygame.sndarray.make_sound(stereo_audio)
        
        # Gold pickup - bright chime
        duration = 0.3
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Multiple frequencies for chime effect
        wave = (np.sin(2 * np.pi * 800 * t) + 
                0.7 * np.sin(2 * np.pi * 1000 * t) +
                0.5 * np.sin(2 * np.pi * 1200 * t))
        envelope = np.exp(-t * 3)
        audio = (wave * envelope * 0.25 * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['gold_pickup'] = pygame.sndarray.make_sound(stereo_audio)
    
    def _generate_ambient_sounds(self, sample_rate: int):
        """Generate ambient background sounds"""
        import numpy as np
        
        # Dungeon ambience - low rumble
        duration = 2.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Low frequency rumble with some variation
        base_freq = 60
        wave = (np.sin(2 * np.pi * base_freq * t) +
                0.5 * np.sin(2 * np.pi * (base_freq * 1.5) * t) +
                0.3 * np.random.normal(0, 0.1, samples))  # Add noise
        
        envelope = np.ones_like(t) * 0.1  # Constant low volume
        audio = (wave * envelope * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['ambient_dungeon'] = pygame.sndarray.make_sound(stereo_audio)
    
    def _generate_magic_sounds(self, sample_rate: int):
        """Generate magical effect sounds"""
        import numpy as np
        
        # Spell cast - ethereal sweep
        duration = 0.4
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Frequency sweep from low to high
        start_freq = 200
        end_freq = 800
        frequency = start_freq + (end_freq - start_freq) * (t / duration)
        
        wave = np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t * 2) * (1 - t / duration)  # Fade in and out
        audio = (wave * envelope * 0.3 * 32767).astype(np.int16)
        
        stereo_audio = np.zeros((samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = audio
        stereo_audio[:, 1] = audio
        
        self.sounds['spell_cast'] = pygame.sndarray.make_sound(stereo_audio)
    
    def _subscribe_to_events(self):
        """Subscribe to game events for audio triggers"""
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ATTACK_CRIT, self._on_attack_crit)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.GOLD_PICKUP, self._on_gold_pickup)
        game_events.subscribe(GameEventType.SPELL_CAST, self._on_spell_cast)
        game_events.subscribe(GameEventType.MOVE_START, self._on_move_start)
        game_events.subscribe(GameEventType.FLOOR_CHANGE, self._on_floor_change)
        game_events.subscribe(GameEventType.MENU_SELECT, self._on_menu_select)
    
    def play_sound(self, sound_name: str, volume: float = 1.0, pitch: float = 1.0, 
                   pan: float = 0.0, layer: bool = True) -> Optional[pygame.mixer.Channel]:
        """Play a sound with optional effects"""
        if not self.audio_available or self.muted or not juice_manager.settings.audio_enabled:
            return None
        
        if sound_name not in self.sounds:
            return None
        
        sound = self.sounds[sound_name]
        
        # Apply volume scaling
        final_volume = volume * self.sfx_volume * self.master_volume * juice_manager.settings.intensity
        
        # Find available channel or use any if layering is disabled
        channel = None
        if layer:
            channel = pygame.mixer.find_channel()
        else:
            channel = pygame.mixer.Channel(0)
        
        if channel:
            # Apply pitch (speed) adjustment if supported
            if pitch != 1.0:
                # Note: pygame doesn't support pitch shifting directly
                # This would require more advanced audio processing
                pass
            
            channel.play(sound)
            channel.set_volume(final_volume)
            
            # Apply panning if supported
            if pan != 0.0:
                left_vol = final_volume * (1.0 - max(0, pan))
                right_vol = final_volume * (1.0 - max(0, -pan))
                channel.set_volume(left_vol, right_vol)
        
        return channel
    
    def play_layered_sound(self, base_sound: str, layer_sounds: List[str], 
                          volumes: List[float] = None) -> List[pygame.mixer.Channel]:
        """Play multiple sounds layered together"""
        channels = []
        
        # Play base sound
        base_channel = self.play_sound(base_sound)
        if base_channel:
            channels.append(base_channel)
        
        # Play layer sounds
        if volumes is None:
            volumes = [0.5] * len(layer_sounds)
        
        for sound, volume in zip(layer_sounds, volumes):
            channel = self.play_sound(sound, volume)
            if channel:
                channels.append(channel)
        
        return channels
    
    def play_random_variant(self, sound_base: str, count: int = 3) -> Optional[pygame.mixer.Channel]:
        """Play a random variant of a sound"""
        variants = [f"{sound_base}_{i}" for i in range(count)]
        available_variants = [v for v in variants if v in self.sounds]
        
        if available_variants:
            chosen = random.choice(available_variants)
            return self.play_sound(chosen)
        else:
            return self.play_sound(sound_base)
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def toggle_mute(self):
        """Toggle audio mute"""
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.pause()
        else:
            pygame.mixer.unpause()
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds"""
        if self.audio_available:
            pygame.mixer.stop()
    
    def _on_attack_hit(self, event):
        """Handle attack hit audio"""
        damage = event.get('damage', 0)
        enemy_type = event.get('enemy_type', '')
        
        # Choose sound based on damage and enemy type
        if damage >= 25:
            self.play_sound('hit_heavy', volume=0.8)
        else:
            self.play_sound('hit_light', volume=0.6)
        
        # Add enemy-specific layer
        if 'skeleton' in enemy_type:
            # Bone clatter sound (using existing sounds as approximation)
            self.play_sound('hit_light', volume=0.3, pitch=1.5)
        elif 'troll' in enemy_type:
            # Deep thud
            self.play_sound('hit_heavy', volume=0.9, pitch=0.8)
    
    def _on_attack_crit(self, event):
        """Handle critical hit audio"""
        # Layered critical hit sound
        self.play_layered_sound('hit_crit', ['hit_light'], [0.4])
    
    def _on_player_hurt(self, event):
        """Handle player hurt audio"""
        damage = event.get('damage', 0)
        
        # Pain sound - use hit sound with different parameters
        volume = min(0.8, 0.4 + damage * 0.02)
        self.play_sound('hit_heavy', volume=volume, pitch=0.7)
    
    def _on_enemy_death(self, event):
        """Handle enemy death audio"""
        enemy_type = event.get('enemy_type', '')
        
        if 'boss' in enemy_type.lower():
            # Epic boss death sound
            self.play_layered_sound('hit_heavy', ['hit_crit', 'spell_cast'], [0.8, 0.6])
        else:
            # Regular enemy death
            self.play_sound('hit_heavy', volume=0.7, pitch=0.6)
    
    def _on_gold_pickup(self, event):
        """Handle gold pickup audio"""
        amount = event.get('amount', 0)
        
        # Scale volume and pitch based on amount
        volume = min(0.8, 0.3 + amount * 0.01)
        pitch = 1.0 + min(amount * 0.005, 0.3)
        
        self.play_sound('gold_pickup', volume=volume, pitch=pitch)
    
    def _on_spell_cast(self, event):
        """Handle spell cast audio"""
        spell_type = event.get('spell_type', 'arcane')
        power = event.get('power', 1)
        
        volume = 0.6 * power
        self.play_sound('spell_cast', volume=volume)
    
    def _on_move_start(self, event):
        """Handle movement audio"""
        # Subtle footstep sound
        self.play_sound('ui_select', volume=0.1, pitch=0.8)
    
    def _on_floor_change(self, event):
        """Handle floor change audio"""
        # Magical transition sound
        self.play_sound('spell_cast', volume=0.8, pitch=1.2)
    
    def _on_menu_select(self, event):
        """Handle menu selection audio"""
        self.play_sound('ui_select', volume=0.5)

class FallbackAudio:
    """Fallback audio system using system beeps"""
    
    def __init__(self):
        self.enabled = True
        self.muted = False
        self.master_volume = 0.7
        
        # Subscribe to events like the main audio manager
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to game events for audio triggers"""
        game_events.subscribe(GameEventType.ATTACK_HIT, self._on_attack_hit)
        game_events.subscribe(GameEventType.ATTACK_CRIT, self._on_attack_crit)
        game_events.subscribe(GameEventType.PLAYER_HURT, self._on_player_hurt)
        game_events.subscribe(GameEventType.ENEMY_DEATH, self._on_enemy_death)
        game_events.subscribe(GameEventType.GOLD_PICKUP, self._on_gold_pickup)
        game_events.subscribe(GameEventType.SPELL_CAST, self._on_spell_cast)
        game_events.subscribe(GameEventType.MOVE_START, self._on_move_start)
        game_events.subscribe(GameEventType.FLOOR_CHANGE, self._on_floor_change)
        game_events.subscribe(GameEventType.MENU_SELECT, self._on_menu_select)
    
    def beep(self, frequency: int = 800, duration: int = 100):
        """System beep fallback"""
        if not self.enabled or self.muted or not juice_manager.settings.audio_enabled:
            return
        
        try:
            # Try different system beep methods
            if os.name == 'nt':  # Windows
                import winsound
                winsound.Beep(frequency, duration)
            else:  # Unix-like systems
                os.system(f'beep -f {frequency} -l {duration} 2>/dev/null')
        except:
            # Silent fallback
            pass
    
    def play_sound(self, sound_name: str, volume: float = 1.0, pitch: float = 1.0, **kwargs):
        """Fallback sound playing"""
        if sound_name in ['hit_light', 'ui_select']:
            self.beep(int(800 * pitch), int(50 * volume * 2))
        elif sound_name in ['hit_heavy']:
            self.beep(int(400 * pitch), int(100 * volume * 2))
        elif sound_name == 'hit_crit':
            self.beep(int(1200 * pitch), int(80 * volume * 2))
        elif sound_name == 'gold_pickup':
            self.beep(int(1000 * pitch), int(80 * volume * 2))
        elif sound_name == 'spell_cast':
            self.beep(int(600 * pitch), int(150 * volume * 2))
        
        return None  # No channel object in fallback
    
    def play_layered_sound(self, base_sound: str, layer_sounds: list, volumes: list = None):
        """Fallback layered sound - just play base sound"""
        return [self.play_sound(base_sound)]
    
    def toggle_mute(self):
        """Toggle audio mute"""
        self.muted = not self.muted
    
    def set_master_volume(self, volume: float):
        """Set master volume"""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def stop_all_sounds(self):
        """Stop all sounds (no-op for fallback)"""
        pass
    
    # Event handlers
    def _on_attack_hit(self, event):
        damage = event.get('damage', 0)
        if damage >= 25:
            self.play_sound('hit_heavy', volume=0.8)
        else:
            self.play_sound('hit_light', volume=0.6)
    
    def _on_attack_crit(self, event):
        self.play_sound('hit_crit', volume=0.8)
    
    def _on_player_hurt(self, event):
        damage = event.get('damage', 0)
        volume = min(0.8, 0.4 + damage * 0.02)
        self.play_sound('hit_heavy', volume=volume, pitch=0.7)
    
    def _on_enemy_death(self, event):
        enemy_type = event.get('enemy_type', '')
        if 'boss' in enemy_type.lower():
            self.play_sound('hit_heavy', volume=1.0, pitch=0.5)
        else:
            self.play_sound('hit_heavy', volume=0.7, pitch=0.6)
    
    def _on_gold_pickup(self, event):
        amount = event.get('amount', 0)
        volume = min(0.8, 0.3 + amount * 0.01)
        pitch = 1.0 + min(amount * 0.005, 0.3)
        self.play_sound('gold_pickup', volume=volume, pitch=pitch)
    
    def _on_spell_cast(self, event):
        power = event.get('power', 1)
        self.play_sound('spell_cast', volume=0.6 * power)
    
    def _on_move_start(self, event):
        self.play_sound('ui_select', volume=0.1, pitch=0.8)
    
    def _on_floor_change(self, event):
        self.play_sound('spell_cast', volume=0.8, pitch=1.2)
    
    def _on_menu_select(self, event):
        self.play_sound('ui_select', volume=0.5)

# Global audio manager
try:
    audio_manager = AudioManager()
    if not audio_manager.audio_available:
        audio_manager = FallbackAudio()
except:
    audio_manager = FallbackAudio()
