"""
Enhanced renderer with juice effects pipeline
"""

import pygame
from typing import Tuple, List, Callable
from .juice_manager import juice_manager
from .ascii_renderer import ASCIIRenderer
from .visual_effects import visual_effects
from .particle_system import particle_system
from .camera_system import camera_manager

class JuiceRenderer:
    """Enhanced renderer with juice effects pipeline"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ascii_renderer = ASCIIRenderer()
        
        # Draw pipeline functions
        self.draw_dungeon_func: Callable = None
        self.draw_entities_func: Callable = None
        self.draw_ui_func: Callable = None
        
        # FX layer (initially empty)
        self.fx_particles = []
        self.fx_text = []
    
    def set_draw_functions(self, draw_dungeon: Callable, draw_entities: Callable, draw_ui: Callable):
        """Set the drawing functions for the pipeline"""
        self.draw_dungeon_func = draw_dungeon
        self.draw_entities_func = draw_entities
        self.draw_ui_func = draw_ui
    
    def render_frame(self):
        """Main render pipeline: clear → drawDungeon → drawEntities → drawFX → flush"""
        # Get camera offset (includes screen shake)
        camera_offset = juice_manager.get_camera_offset()
        
        # Clear screen
        self.screen.fill(self.ascii_renderer.colors.get("background", (20, 20, 30)))
        
        # Apply camera offset for shake effect
        if camera_offset != (0, 0):
            # Create offset surface for shake effect
            offset_surface = pygame.Surface(self.screen.get_size())
            offset_surface.fill(self.ascii_renderer.colors.get("background", (20, 20, 30)))
            
            # Draw to offset surface
            temp_screen = self.screen
            self.screen = offset_surface
        
        # Draw dungeon
        if self.draw_dungeon_func:
            self.draw_dungeon_func()
        
        # Draw entities
        if self.draw_entities_func:
            self.draw_entities_func()
        
        # Draw FX layer
        self.draw_fx()
        
        # Draw UI (not affected by camera shake)
        if camera_offset != (0, 0):
            # Restore original screen and blit with offset
            original_screen = temp_screen
            self.screen = original_screen
            self.screen.blit(offset_surface, camera_offset)
        
        # Draw UI on top (not shaken)
        if self.draw_ui_func:
            self.draw_ui_func()
        
        # Draw screen flash effects
        self._draw_screen_flash()
        
        # Draw lighting effects
        self._draw_lighting_effects()
        
        # Draw debug overlay if enabled
        if juice_manager.settings.debug_overlay_enabled:
            self.draw_debug_overlay()
    
    def _draw_lighting_effects(self):
        """Draw lighting and focus effects"""
        if not camera_manager:
            return
        
        lighting_data = camera_manager.get_lighting_data()
        
        # Draw focus flashes
        for flash in lighting_data.get('focus_flashes', []):
            self._draw_focus_flash(flash)
        
        # Draw vignette
        vignette_data = lighting_data.get('vignette')
        if vignette_data:
            self._draw_vignette(vignette_data)
        
        # Draw color overlay
        overlay_data = lighting_data.get('color_overlay')
        if overlay_data:
            self._draw_color_overlay(overlay_data)
    
    def _draw_focus_flash(self, flash_data: dict):
        """Draw a focus flash effect"""
        world_x = flash_data.get('world_x', flash_data.get('x', 0))  # Backward compatibility
        world_y = flash_data.get('world_y', flash_data.get('y', 0))
        color = flash_data['color']
        intensity = flash_data['intensity']
        radius = flash_data.get('radius', 50)
        
        # Apply camera offset to get screen position
        camera_x, camera_y = camera_manager.get_camera_position() if camera_manager else (0, 0)
        screen_x = world_x + camera_x
        screen_y = world_y + camera_y
        
        # Skip if off-screen (simple culling)
        if (screen_x < -radius or screen_x > self.screen.get_width() + radius or
            screen_y < -radius or screen_y > self.screen.get_height() + radius):
            return
        
        # Create flash surface
        flash_surface = pygame.Surface((radius * 2, radius * 2))
        flash_surface.set_colorkey((0, 0, 0))
        
        # Draw radial gradient flash
        for r in range(radius, 0, -2):
            alpha = intensity * (1.0 - r / radius) * 255
            flash_color = (*color, int(alpha))
            pygame.draw.circle(flash_surface, color, (radius, radius), r)
        
        flash_surface.set_alpha(int(intensity * 255))
        
        # Draw flash at screen position
        flash_rect = flash_surface.get_rect(center=(int(screen_x), int(screen_y)))
        self.screen.blit(flash_surface, flash_rect, special_flags=pygame.BLEND_ADD)
    
    def _draw_vignette(self, vignette_data: dict):
        """Draw vignette effect"""
        intensity = vignette_data['intensity']
        color = vignette_data['color']
        
        # Create vignette surface
        vignette_surface = pygame.Surface(self.screen.get_size())
        vignette_surface.fill(color)
        
        # Create radial mask
        center_x, center_y = self.screen.get_width() // 2, self.screen.get_height() // 2
        max_radius = max(center_x, center_y)
        
        for y in range(self.screen.get_height()):
            for x in range(self.screen.get_width()):
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                alpha = min(255, int((distance / max_radius) * intensity * 255))
                vignette_surface.set_at((x, y), (*color, alpha))
        
        # Apply vignette
        self.screen.blit(vignette_surface, (0, 0), special_flags=pygame.BLEND_MULT)
    
    def _draw_color_overlay(self, overlay_data: dict):
        """Draw color overlay effect"""
        color = overlay_data['color']
        alpha = overlay_data['alpha']
        
        # Create overlay surface
        overlay_surface = pygame.Surface(self.screen.get_size())
        overlay_surface.fill(color)
        overlay_surface.set_alpha(int(alpha * 255))
        
        # Blend with screen
        self.screen.blit(overlay_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def _draw_screen_flash(self):
        """Draw screen flash effects"""
        flash_data = visual_effects.get_screen_flash_data()
        if flash_data:
            # Create flash surface
            flash_surface = pygame.Surface(self.screen.get_size())
            flash_surface.fill(flash_data['color'])
            flash_surface.set_alpha(int(flash_data['alpha'] * 255))
            
            # Blend with screen
            self.screen.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def draw_fx(self):
        """Draw all FX effects (particles, floating text, etc.)"""
        # Draw particles
        particles = particle_system.get_particles_for_render()
        for particle_data in particles:
            self._draw_particle(particle_data)
        
        # Draw enhanced text effects
        text_effects = particle_system.get_text_effects_for_render()
        for text_data in text_effects:
            self._draw_enhanced_text(text_data)
    
    def _draw_particle(self, particle_data: dict):
        """Draw a single particle"""
        x = particle_data['x']
        y = particle_data['y']
        glyph = particle_data['glyph']
        color = particle_data['color']
        scale = particle_data.get('scale', 1.0)
        rotation = particle_data.get('rotation', 0.0)
        
        # Skip if color is too faded
        if sum(color) < 10:
            return
        
        # Create text surface
        font = self.ascii_renderer.small_font
        if scale > 1.2:
            font = self.ascii_renderer.ui_font
        
        text_surface = font.render(glyph, True, color)
        
        # Apply scaling
        if scale != 1.0:
            new_size = (int(text_surface.get_width() * scale), 
                       int(text_surface.get_height() * scale))
            text_surface = pygame.transform.scale(text_surface, new_size)
        
        # Apply rotation
        if rotation != 0.0:
            text_surface = pygame.transform.rotate(text_surface, rotation)
        
        # Draw with center alignment
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)
    
    def _draw_enhanced_text(self, text_data: dict):
        """Draw enhanced floating text"""
        x = text_data['x']
        y = text_data['y']
        text = text_data['text']
        color = text_data['color']
        font_size = text_data.get('font_size', 'normal')
        scale = text_data.get('scale', 1.0)
        rotation = text_data.get('rotation', 0.0)
        
        # Skip if color is too faded
        if sum(color) < 10:
            return
        
        # Choose font
        if font_size == "large":
            font = self.ascii_renderer.ui_font
        elif font_size == "small":
            font = self.ascii_renderer.small_font
        else:
            font = self.ascii_renderer.tile_font
        
        # Create text surface
        text_surface = font.render(text, True, color)
        
        # Apply scaling
        if scale != 1.0:
            new_size = (int(text_surface.get_width() * scale), 
                       int(text_surface.get_height() * scale))
            text_surface = pygame.transform.scale(text_surface, new_size)
        
        # Apply rotation
        if rotation != 0.0:
            text_surface = pygame.transform.rotate(text_surface, rotation)
        
        # Add outline for better visibility
        if font_size == "large" or scale > 1.2:
            outline_surface = font.render(text, True, (0, 0, 0))
            if scale != 1.0:
                outline_surface = pygame.transform.scale(outline_surface, new_size)
            if rotation != 0.0:
                outline_surface = pygame.transform.rotate(outline_surface, rotation)
            
            # Draw outline
            outline_rect = outline_surface.get_rect(center=(x, y))
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                offset_rect = outline_rect.copy()
                offset_rect.x += dx
                offset_rect.y += dy
                self.screen.blit(outline_surface, offset_rect)
        
        # Draw main text
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)
    
    def draw_debug_overlay(self):
        """Draw debug information overlay"""
        debug_info = juice_manager.debug_info
        y_offset = 10
        
        debug_texts = [
            f"FPS: {debug_info['fps']:.1f}",
            f"Particles: {debug_info['particles']}",
            f"Shake: {'ON' if debug_info['active_shakes'] > 0 else 'OFF'}",
            f"Paused: {'YES' if debug_info['paused_frames'] > 0 else 'NO'}",
            f"Juice: {juice_manager.settings.intensity:.1f}"
        ]
        
        for text in debug_texts:
            self.ascii_renderer.render_text(
                self.screen, text, 10, y_offset, "small", "ui_text"
            )
            y_offset += 20
