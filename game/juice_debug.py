"""
Comprehensive debugging and tuning tools for the juice system
"""

import pygame
import time
import json
import os
from typing import Dict, List, Any, Optional
from .juice_manager import juice_manager
from .particle_system import particle_system
from .visual_effects import visual_effects
from .audio_system import audio_manager
from .camera_system import camera_manager
from .game_events import game_events, GameEventType

class JuiceProfiler:
    """Performance profiler for juice effects"""
    
    def __init__(self):
        self.frame_times = []
        self.effect_counts = {}
        self.max_samples = 300  # 5 seconds at 60fps
        self.start_time = 0.0
        self.enabled = False
    
    def start_frame(self):
        """Start timing a frame"""
        if self.enabled:
            self.start_time = time.perf_counter()
    
    def end_frame(self):
        """End timing a frame and record data"""
        if not self.enabled:
            return
        
        frame_time = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
        self.frame_times.append(frame_time)
        
        # Keep only recent samples
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)
        
        # Record effect counts
        self.effect_counts = {
            'particles': particle_system.get_particle_count(),
            'text_effects': particle_system.get_text_effect_count(),
            'screen_shakes': len(juice_manager.screen_shake.shake_layers),
            'focus_flashes': len(camera_manager.lighting_effects.get_focus_flashes()) if camera_manager else 0,
            'fps': juice_manager.frame_clock.get_fps()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.frame_times:
            return {}
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        min_frame_time = min(self.frame_times)
        max_frame_time = max(self.frame_times)
        
        return {
            'avg_frame_time_ms': avg_frame_time,
            'min_frame_time_ms': min_frame_time,
            'max_frame_time_ms': max_frame_time,
            'avg_fps': 1000.0 / avg_frame_time if avg_frame_time > 0 else 0,
            'frame_samples': len(self.frame_times),
            'effect_counts': self.effect_counts.copy()
        }
    
    def reset(self):
        """Reset profiler data"""
        self.frame_times.clear()
        self.effect_counts.clear()

class JuiceRecorder:
    """Records and replays juice events for testing"""
    
    def __init__(self):
        self.recording = False
        self.recorded_events = []
        self.playback_events = []
        self.playback_index = 0
        self.start_time = 0.0
        
        # Subscribe to all events for recording
        for event_type in GameEventType:
            game_events.subscribe(event_type, self._record_event)
    
    def start_recording(self):
        """Start recording events"""
        self.recording = True
        self.recorded_events.clear()
        self.start_time = time.time()
    
    def stop_recording(self):
        """Stop recording events"""
        self.recording = False
    
    def _record_event(self, event):
        """Record an event with timestamp"""
        if not self.recording:
            return
        
        self.recorded_events.append({
            'type': event.type.value,
            'data': event.data.copy(),
            'timestamp': time.time() - self.start_time
        })
    
    def save_recording(self, filename: str):
        """Save recorded events to file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'events': self.recorded_events,
                    'juice_settings': {
                        'intensity': juice_manager.settings.intensity,
                        'enabled': juice_manager.settings.enabled,
                        'hit_stop_enabled': juice_manager.settings.hit_stop_enabled,
                        'screen_shake_enabled': juice_manager.settings.screen_shake_enabled,
                        'smooth_movement_enabled': juice_manager.settings.smooth_movement_enabled,
                        'particles_enabled': juice_manager.settings.particles_enabled,
                        'audio_enabled': juice_manager.settings.audio_enabled,
                        'smart_camera_enabled': juice_manager.settings.smart_camera_enabled,
                        'focus_flash_enabled': juice_manager.settings.focus_flash_enabled
                    }
                }, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save recording: {e}")
            return False
    
    def load_recording(self, filename: str):
        """Load recorded events from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.playback_events = data.get('events', [])
                self.playback_index = 0
                
                # Optionally restore juice settings
                settings = data.get('juice_settings', {})
                if settings:
                    juice_manager.settings.intensity = settings.get('intensity', 1.0)
                    juice_manager.settings.enabled = settings.get('enabled', True)
                    # ... restore other settings
                
            return True
        except Exception as e:
            print(f"Failed to load recording: {e}")
            return False
    
    def start_playback(self):
        """Start playing back recorded events"""
        self.playback_index = 0
        self.start_time = time.time()
    
    def update_playback(self):
        """Update playback - call this every frame"""
        if self.playback_index >= len(self.playback_events):
            return
        
        current_time = time.time() - self.start_time
        
        while (self.playback_index < len(self.playback_events) and 
               self.playback_events[self.playback_index]['timestamp'] <= current_time):
            
            event_data = self.playback_events[self.playback_index]
            
            # Recreate and emit the event
            try:
                event_type = GameEventType(event_data['type'])
                game_events.emit(event_type, event_data['data'])
            except ValueError:
                print(f"Unknown event type: {event_data['type']}")
            
            self.playback_index += 1

class JuiceDebugOverlay:
    """Advanced debug overlay with detailed information"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.enabled = False
        self.show_graphs = False
        self.show_settings = False
        
        # Graph data
        self.fps_history = []
        self.particle_history = []
        self.max_history = 120  # 2 seconds at 60fps
    
    def toggle(self):
        """Toggle debug overlay"""
        self.enabled = not self.enabled
    
    def toggle_graphs(self):
        """Toggle performance graphs"""
        self.show_graphs = not self.show_graphs
    
    def toggle_settings(self):
        """Toggle settings panel"""
        self.show_settings = not self.show_settings
    
    def update(self, profiler: JuiceProfiler):
        """Update debug data"""
        if not self.enabled:
            return
        
        # Update history
        stats = profiler.get_stats()
        if stats:
            self.fps_history.append(stats.get('avg_fps', 0))
            self.particle_history.append(stats['effect_counts'].get('particles', 0))
            
            # Limit history
            if len(self.fps_history) > self.max_history:
                self.fps_history.pop(0)
            if len(self.particle_history) > self.max_history:
                self.particle_history.pop(0)
    
    def render(self, profiler: JuiceProfiler):
        """Render debug overlay"""
        if not self.enabled:
            return
        
        y_offset = 10
        
        # Basic stats
        y_offset = self._render_basic_stats(profiler, y_offset)
        
        # Juice settings
        if self.show_settings:
            y_offset = self._render_juice_settings(y_offset)
        
        # Performance graphs
        if self.show_graphs:
            self._render_performance_graphs()
        
        # Controls help
        self._render_controls_help()
    
    def _render_basic_stats(self, profiler: JuiceProfiler, y_offset: int) -> int:
        """Render basic performance stats"""
        stats = profiler.get_stats()
        if not stats:
            return y_offset
        
        # Background panel
        panel_height = 140
        panel_surface = pygame.Surface((300, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((0, 0, 0))
        self.screen.blit(panel_surface, (10, y_offset))
        
        # Stats text
        texts = [
            f"FPS: {stats.get('avg_fps', 0):.1f} (avg: {stats.get('avg_frame_time_ms', 0):.2f}ms)",
            f"Frame Time: {stats.get('min_frame_time_ms', 0):.2f}-{stats.get('max_frame_time_ms', 0):.2f}ms",
            f"Particles: {stats['effect_counts'].get('particles', 0)}",
            f"Text Effects: {stats['effect_counts'].get('text_effects', 0)}",
            f"Screen Shakes: {stats['effect_counts'].get('screen_shakes', 0)}",
            f"Focus Flashes: {stats['effect_counts'].get('focus_flashes', 0)}",
            f"Juice Intensity: {juice_manager.settings.intensity:.1f}"
        ]
        
        for i, text in enumerate(texts):
            color = (255, 255, 255)
            if "FPS:" in text and stats.get('avg_fps', 0) < 30:
                color = (255, 100, 100)  # Red for low FPS
            elif "Particles:" in text and stats['effect_counts'].get('particles', 0) > 150:
                color = (255, 255, 100)  # Yellow for high particle count
            
            text_surface = self.font.render(text, True, color)
            self.screen.blit(text_surface, (15, y_offset + 5 + i * 18))
        
        return y_offset + panel_height + 10
    
    def _render_juice_settings(self, y_offset: int) -> int:
        """Render juice settings panel"""
        settings = juice_manager.settings
        
        # Background panel
        panel_height = 180
        panel_surface = pygame.Surface((280, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((20, 20, 40))
        self.screen.blit(panel_surface, (10, y_offset))
        
        # Settings text
        texts = [
            "JUICE SETTINGS:",
            f"Master: {'ON' if settings.enabled else 'OFF'}",
            f"Hit-Stop: {'ON' if settings.hit_stop_enabled else 'OFF'}",
            f"Screen Shake: {'ON' if settings.screen_shake_enabled else 'OFF'}",
            f"Smooth Movement: {'ON' if settings.smooth_movement_enabled else 'OFF'}",
            f"Particles: {'ON' if settings.particles_enabled else 'OFF'}",
            f"Audio: {'ON' if settings.audio_enabled else 'OFF'}",
            f"Smart Camera: {'ON' if settings.smart_camera_enabled else 'OFF'}",
            f"Focus Flash: {'ON' if settings.focus_flash_enabled else 'OFF'}"
        ]
        
        for i, text in enumerate(texts):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            if "OFF" in text:
                color = (150, 150, 150)
            
            text_surface = self.small_font.render(text, True, color)
            self.screen.blit(text_surface, (15, y_offset + 5 + i * 18))
        
        return y_offset + panel_height + 10
    
    def _render_performance_graphs(self):
        """Render performance graphs"""
        if not self.fps_history or not self.particle_history:
            return
        
        graph_width = 200
        graph_height = 60
        graph_x = self.screen.get_width() - graph_width - 10
        graph_y = 10
        
        # FPS graph
        self._render_graph(self.fps_history, graph_x, graph_y, graph_width, graph_height,
                          "FPS", (100, 255, 100), max_val=120)
        
        # Particle graph
        self._render_graph(self.particle_history, graph_x, graph_y + graph_height + 20,
                          graph_width, graph_height, "Particles", (255, 100, 100), max_val=200)
    
    def _render_graph(self, data: List[float], x: int, y: int, width: int, height: int,
                     title: str, color: tuple, max_val: float):
        """Render a single performance graph"""
        # Background
        graph_surface = pygame.Surface((width, height))
        graph_surface.set_alpha(200)
        graph_surface.fill((0, 0, 0))
        self.screen.blit(graph_surface, (x, y))
        
        # Title
        title_surface = self.small_font.render(title, True, (255, 255, 255))
        self.screen.blit(title_surface, (x + 5, y + 2))
        
        # Graph data
        if len(data) > 1:
            points = []
            for i, value in enumerate(data):
                graph_x = x + (i / len(data)) * width
                graph_y = y + height - (value / max_val) * (height - 20)
                points.append((graph_x, max(y + 20, graph_y)))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Current value
        if data:
            current_val = data[-1]
            val_text = f"{current_val:.1f}"
            val_surface = self.small_font.render(val_text, True, color)
            self.screen.blit(val_surface, (x + width - 40, y + height - 18))
    
    def _render_controls_help(self):
        """Render controls help"""
        help_texts = [
            "F1: Toggle Debug | F2: Toggle Juice | F3/F4: Intensity",
            "F5: Particles | F6: Clear | F7/F8: Audio | F9/F10: Camera",
            "Ctrl+G: Graphs | Ctrl+S: Settings | Ctrl+R: Record"
        ]
        
        y_start = self.screen.get_height() - 60
        
        for i, text in enumerate(help_texts):
            text_surface = self.small_font.render(text, True, (150, 150, 150))
            self.screen.blit(text_surface, (10, y_start + i * 16))

class JuiceTuner:
    """Interactive juice parameter tuning"""
    
    def __init__(self):
        self.profiler = JuiceProfiler()
        self.recorder = JuiceRecorder()
        self.debug_overlay = None  # Will be set by game engine
        
        # Tuning presets
        self.presets = {
            'minimal': {
                'intensity': 0.3,
                'hit_stop_enabled': True,
                'screen_shake_enabled': False,
                'particles_enabled': False,
                'audio_enabled': True
            },
            'balanced': {
                'intensity': 0.7,
                'hit_stop_enabled': True,
                'screen_shake_enabled': True,
                'particles_enabled': True,
                'audio_enabled': True
            },
            'maximum': {
                'intensity': 1.0,
                'hit_stop_enabled': True,
                'screen_shake_enabled': True,
                'particles_enabled': True,
                'audio_enabled': True,
                'smart_camera_enabled': True,
                'focus_flash_enabled': True
            }
        }
    
    def apply_preset(self, preset_name: str):
        """Apply a juice preset"""
        if preset_name not in self.presets:
            return False
        
        preset = self.presets[preset_name]
        settings = juice_manager.settings
        
        for key, value in preset.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        return True
    
    def save_current_as_preset(self, name: str):
        """Save current settings as a preset"""
        settings = juice_manager.settings
        self.presets[name] = {
            'intensity': settings.intensity,
            'enabled': settings.enabled,
            'hit_stop_enabled': settings.hit_stop_enabled,
            'screen_shake_enabled': settings.screen_shake_enabled,
            'smooth_movement_enabled': settings.smooth_movement_enabled,
            'particles_enabled': settings.particles_enabled,
            'audio_enabled': settings.audio_enabled,
            'smart_camera_enabled': settings.smart_camera_enabled,
            'focus_flash_enabled': settings.focus_flash_enabled
        }
    
    def get_performance_report(self) -> str:
        """Get a detailed performance report"""
        stats = self.profiler.get_stats()
        if not stats:
            return "No performance data available"
        
        report = f"""
JUICE PERFORMANCE REPORT
========================
Average FPS: {stats.get('avg_fps', 0):.1f}
Frame Time: {stats.get('avg_frame_time_ms', 0):.2f}ms (avg)
Frame Time Range: {stats.get('min_frame_time_ms', 0):.2f}-{stats.get('max_frame_time_ms', 0):.2f}ms

EFFECT COUNTS:
- Particles: {stats['effect_counts'].get('particles', 0)}
- Text Effects: {stats['effect_counts'].get('text_effects', 0)}
- Screen Shakes: {stats['effect_counts'].get('screen_shakes', 0)}
- Focus Flashes: {stats['effect_counts'].get('focus_flashes', 0)}

JUICE SETTINGS:
- Master Intensity: {juice_manager.settings.intensity:.1f}
- Effects Enabled: {juice_manager.settings.enabled}
- Hit-Stop: {juice_manager.settings.hit_stop_enabled}
- Screen Shake: {juice_manager.settings.screen_shake_enabled}
- Particles: {juice_manager.settings.particles_enabled}
- Audio: {juice_manager.settings.audio_enabled}

RECOMMENDATIONS:
"""
        
        # Add performance recommendations
        if stats.get('avg_fps', 0) < 30:
            report += "- Consider reducing juice intensity or disabling particles\n"
        if stats['effect_counts'].get('particles', 0) > 150:
            report += "- High particle count detected, consider limiting spawns\n"
        if stats.get('avg_frame_time_ms', 0) > 20:
            report += "- Frame time is high, check for performance bottlenecks\n"
        
        return report

# Global juice tuner instance
juice_tuner = JuiceTuner()
