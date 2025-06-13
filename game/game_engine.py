"""
Main game engine that coordinates all game systems
"""

import pygame
from typing import Optional
from .constants import *
from .player import Player
from .dungeon import Dungeon
from .enemy import CombatSystem
from .fog_of_war import FogOfWar
from .hex_grid import HexGrid
from .ascii_renderer import ASCIIRenderer
from .game_events import GameEventType, game_events
from .juice_manager import juice_manager
from .juice_renderer import JuiceRenderer
from .movement_system import EnhancedPlayer
from .visual_effects import visual_effects
from .particle_system import particle_system
from .audio_system import audio_manager
from .camera_system import CameraManager
from .juice_debug import juice_tuner, JuiceDebugOverlay


class GameEngine:
    """Main game engine class"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # ASCII renderer for retro styling
        self.ascii_renderer = ASCIIRenderer()
        
        # Juice renderer with effects pipeline
        self.juice_renderer = JuiceRenderer(screen)
        self.juice_renderer.set_draw_functions(
            self._draw_dungeon,
            self._draw_entities, 
            self._draw_ui
        )
        
        # Enhanced camera system
        self.camera_manager = CameraManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Set global camera manager reference
        from . import camera_system
        camera_system.camera_manager = self.camera_manager
        
        # Debug and tuning tools
        self.debug_overlay = JuiceDebugOverlay(screen)
        juice_tuner.debug_overlay = self.debug_overlay
        juice_tuner.profiler.enabled = True

        # Game state
        self.current_floor = 1
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player = EnhancedPlayer(*self.dungeon.player_start)
        # Message system
        self.message = ""
        self.message_timer = 0.0
        self.message_type = "info"
        self.floating_messages = []  # List of floating messages
        
        self.game_over = False
        self.enemies_defeated = 0  # Track defeated enemies

        # Combat state
        self.in_combat = False
        self.combat_log = []
        self.combat_log_timer = 0.0

        # Mouse interaction
        self.hovered_hex = None

        # Camera/view
        self.camera_x = 0
        self.camera_y = 0
        self.camera_follow_timer = 0.0
        self.camera_follow_duration = 0.5
        self.camera_start_pos = None
        self.camera_target_pos = None
        self.camera_following = False

        # Fog of war
        self.fog_of_war = FogOfWar()
        self.fog_of_war.update_visibility(self.player.q, self.player.r, self.dungeon)
        self.god_mode = False  # Toggle for fog of war

        self._center_camera_on_player()

    def _center_camera_on_player(self, animate: bool = False):
        """Center the camera on the player using enhanced camera system"""
        self.camera_manager.center_on_player(self.player.q, self.player.r)
        self.camera_x, self.camera_y = self.camera_manager.get_camera_position()

    def handle_event(self, event: pygame.event.Event):
        """Handle input events"""
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._restart_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._restart_game()
            return
        
        # God mode toggle (works during gameplay)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:  # Press 'G' to toggle god mode
                self.god_mode = not self.god_mode
                if self.god_mode:
                    self._show_message("God Mode: ON (Fog of War disabled)", "success")
                else:
                    self._show_message("God Mode: OFF (Fog of War enabled)", "info")
                return
            
            # Juice controls
            elif event.key == pygame.K_F1:  # F1 to toggle debug overlay
                juice_manager.toggle_debug()
                return
            elif event.key == pygame.K_F2:  # F2 to toggle all juice effects
                juice_manager.toggle_juice()
                status = "ON" if juice_manager.settings.enabled else "OFF"
                self._show_message(f"Juice Effects: {status}", "info")
                return
            elif event.key == pygame.K_F3:  # F3 to decrease juice intensity
                new_intensity = max(0.0, juice_manager.settings.intensity - 0.2)
                juice_manager.set_intensity(new_intensity)
                self._show_message(f"Juice Intensity: {new_intensity:.1f}", "info")
                return
            elif event.key == pygame.K_F4:  # F4 to increase juice intensity
                new_intensity = min(1.0, juice_manager.settings.intensity + 0.2)
                juice_manager.set_intensity(new_intensity)
                self._show_message(f"Juice Intensity: {new_intensity:.1f}", "info")
                return
            elif event.key == pygame.K_F5:  # F5 to toggle particles
                juice_manager.settings.particles_enabled = not juice_manager.settings.particles_enabled
                status = "ON" if juice_manager.settings.particles_enabled else "OFF"
                self._show_message(f"Particles: {status}", "info")
                return
            elif event.key == pygame.K_F6:  # F6 to clear all particles
                particle_system.clear_all()
                self._show_message("Particles cleared", "info")
                return
            elif event.key == pygame.K_F7:  # F7 to toggle audio
                juice_manager.settings.audio_enabled = not juice_manager.settings.audio_enabled
                status = "ON" if juice_manager.settings.audio_enabled else "OFF"
                self._show_message(f"Audio: {status}", "info")
                return
            elif event.key == pygame.K_F8:  # F8 to toggle audio mute
                audio_manager.toggle_mute()
                status = "MUTED" if audio_manager.muted else "UNMUTED"
                self._show_message(f"Audio: {status}", "info")
                return
            elif event.key == pygame.K_F9:  # F9 to toggle smart camera
                juice_manager.settings.smart_camera_enabled = not juice_manager.settings.smart_camera_enabled
                status = "ON" if juice_manager.settings.smart_camera_enabled else "OFF"
                self._show_message(f"Smart Camera: {status}", "info")
                return
            elif event.key == pygame.K_F10:  # F10 to toggle focus flash
                juice_manager.settings.focus_flash_enabled = not juice_manager.settings.focus_flash_enabled
                status = "ON" if juice_manager.settings.focus_flash_enabled else "OFF"
                self._show_message(f"Focus Flash: {status}", "info")
                return
            elif event.key == pygame.K_F11:  # F11 to toggle hit flash (for the blinking issue)
                # Toggle hit flash effects specifically
                visual_effects.hit_flash.flashes.clear()  # Clear current flashes
                # This is a quick toggle - we could add a proper setting if needed
                self._show_message("Hit flashes cleared", "info")
                return
            
            # Advanced debug controls (with modifiers)
            elif event.key == pygame.K_g and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+G: Toggle performance graphs
                self.debug_overlay.toggle_graphs()
                status = "ON" if self.debug_overlay.show_graphs else "OFF"
                self._show_message(f"Performance Graphs: {status}", "info")
                return
            elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+S: Toggle settings panel
                self.debug_overlay.toggle_settings()
                status = "ON" if self.debug_overlay.show_settings else "OFF"
                self._show_message(f"Settings Panel: {status}", "info")
                return
            elif event.key == pygame.K_r and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+R: Toggle recording
                if juice_tuner.recorder.recording:
                    juice_tuner.recorder.stop_recording()
                    self._show_message("Recording stopped", "info")
                else:
                    juice_tuner.recorder.start_recording()
                    self._show_message("Recording started", "info")
                return
            elif event.key == pygame.K_p and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+P: Performance report
                report = juice_tuner.get_performance_report()
                print(report)  # Print to console
                self._show_message("Performance report printed to console", "info")
                return
            elif event.key == pygame.K_1 and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+1: Apply minimal preset
                juice_tuner.apply_preset('minimal')
                self._show_message("Applied minimal juice preset", "info")
                return
            elif event.key == pygame.K_2 and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+2: Apply balanced preset
                juice_tuner.apply_preset('balanced')
                self._show_message("Applied balanced juice preset", "info")
                return
            elif event.key == pygame.K_3 and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+3: Apply maximum preset
                juice_tuner.apply_preset('maximum')
                self._show_message("Applied maximum juice preset", "info")
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if not self.player.is_moving:
                # Convert mouse position to hex coordinates
                mouse_x, mouse_y = event.pos
                target_q, target_r = HexGrid.pixel_to_hex(
                    mouse_x, mouse_y, self.camera_x, self.camera_y
                )

                # Check if clicked hex is adjacent to player
                neighbors = HexGrid.get_hex_neighbors(self.player.q, self.player.r)

                if (target_q, target_r) in neighbors:
                    # Try to move to adjacent hex
                    self._try_move_player(target_q, target_r)
                elif (target_q, target_r) == (self.player.q, self.player.r):
                    # Clicked on player - show info or do nothing
                    pass

        elif event.type == pygame.MOUSEMOTION:
            # Update hovered hex for visual feedback
            if not self.player.is_moving:
                mouse_x, mouse_y = event.pos
                hovered_q, hovered_r = HexGrid.pixel_to_hex(
                    mouse_x, mouse_y, self.camera_x, self.camera_y
                )

                # Only highlight if it's an adjacent walkable tile
                neighbors = HexGrid.get_hex_neighbors(self.player.q, self.player.r)
                if (hovered_q, hovered_r) in neighbors and self.dungeon.is_walkable(
                    hovered_q, hovered_r
                ):
                    self.hovered_hex = (hovered_q, hovered_r)
                else:
                    self.hovered_hex = None

    def _try_move_player(self, target_q: int, target_r: int):
        """Try to move the player to target position"""
        if self.dungeon.is_walkable(target_q, target_r):
            # Emit move start event
            game_events.emit(GameEventType.MOVE_START, {
                'from_q': self.player.q,
                'from_r': self.player.r,
                'to_q': target_q,
                'to_r': target_r
            })
            
            # Move player
            self.player.move_to(target_q, target_r, self.camera_x, self.camera_y)

            # Interact with tile
            message = self.dungeon.interact_with_tile(target_q, target_r, self.player)

            if message == "enemy":
                self._start_combat(target_q, target_r)
            elif message == "stairs_down":
                self._go_to_next_floor()
            elif message and message.startswith("Found") and "gold" in message:
                # Gold collection - show floating message in gold color
                gold_amount = message.split()[1]  # Extract amount
                self._show_floating_message_at_player(f"+{gold_amount} Gold!", "gold")
                self._show_message(f"Gold collected! Total: {self.player.gold}", "success", 2.0)
                
                # Emit gold pickup event
                game_events.emit(GameEventType.GOLD_PICKUP, {
                    'amount': int(gold_amount),
                    'total': self.player.gold,
                    'q': target_q,
                    'r': target_r
                })
            elif message:
                self._show_message(message, "info")

            # Check if player died
            if self.player.health <= 0:
                self.game_over = True
                self._show_message("You died! Press R to restart or ESC for menu.", "error", 10.0)
                
                # Emit player death event
                game_events.emit(GameEventType.PLAYER_DEATH, {
                    'floor': self.current_floor,
                    'gold': self.player.gold,
                    'player_q': self.player.q,
                    'player_r': self.player.r
                })

            # Start camera follow animation after player starts moving
            # We'll trigger this in the update loop when player finishes moving

    def _start_combat(self, enemy_q: int, enemy_r: int):
        """Start combat with enemy at position"""
        enemy = self.dungeon.get_enemy(enemy_q, enemy_r)
        if enemy and enemy.alive:
            self.in_combat = True

            # Emit attack start event
            game_events.emit(GameEventType.ATTACK_START, {
                'enemy_type': enemy.enemy_type,
                'enemy_q': enemy_q,
                'enemy_r': enemy_r
            })

            # Run combat
            combat_result = CombatSystem.initiate_combat(self.player, enemy)
            self.combat_log = combat_result["log"]
            self.combat_log_timer = 5.0  # Show combat log for 5 seconds
            
            # Show floating damage numbers and emit events
            for damage_event in combat_result.get("damage_events", []):
                if damage_event['type'] == 'damage_dealt':
                    # Show damage dealt to enemy
                    self._show_floating_damage_at_position(
                        damage_event['amount'], 
                        damage_event['position'][0], 
                        damage_event['position'][1],
                        "damage_dealt"
                    )
                    
                    # Emit attack hit event
                    game_events.emit(GameEventType.ATTACK_HIT, {
                        'damage': damage_event['amount'],
                        'enemy_type': enemy.enemy_type,
                        'target_q': damage_event['position'][0],
                        'target_r': damage_event['position'][1]
                    })
                    
                elif damage_event['type'] == 'damage_received':
                    # Show damage received by player
                    self._show_floating_damage_at_position(
                        damage_event['amount'], 
                        damage_event['position'][0], 
                        damage_event['position'][1],
                        "damage_received"
                    )
                    
                    # Emit player hurt event
                    game_events.emit(GameEventType.PLAYER_HURT, {
                        'damage': damage_event['amount'],
                        'enemy_type': enemy.enemy_type,
                        'remaining_health': self.player.health,
                        'player_q': self.player.q,
                        'player_r': self.player.r
                    })

            if combat_result["player_died"]:
                self.game_over = True
                self._show_message("You died in combat! Press R to restart or ESC for menu.", "error", 10.0)
                
                # Emit player death event
                game_events.emit(GameEventType.PLAYER_DEATH, {
                    'cause': 'combat',
                    'enemy_type': enemy.enemy_type,
                    'floor': self.current_floor,
                    'player_q': self.player.q,
                    'player_r': self.player.r
                })
                
            elif combat_result["player_won"]:
                # Remove defeated enemy
                del self.dungeon.enemies[(enemy_q, enemy_r)]
                self.enemies_defeated += 1  # Track defeated enemies
                
                # Emit enemy death event
                game_events.emit(GameEventType.ENEMY_DEATH, {
                    'enemy_type': enemy.enemy_type,
                    'q': enemy_q,
                    'r': enemy_r,
                    'gold_reward': enemy.gold_reward
                })

            self.in_combat = False

    def _process_turn(self):
        """Process a game turn after player moves"""
        if not self.game_over and not self.in_combat:
            # Update all enemies (turn-based)
            self.dungeon.process_enemy_turns(self.player.q, self.player.r)

    def _go_to_next_floor(self):
        """Move to the next dungeon floor"""
        old_health = self.player.health
        old_floor = self.current_floor
        
        self.current_floor += 1
        self.player.go_to_next_floor()
        
        # Show health restoration if any
        health_gained = self.player.health - old_health
        if health_gained > 0:
            self._show_floating_message_at_player(f"+{health_gained} Health!", "heal")

        # Generate new dungeon
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player.q, self.player.r = self.dungeon.player_start

        # Reset fog of war for new floor
        self.fog_of_war = FogOfWar()
        self.fog_of_war.update_visibility(self.player.q, self.player.r, self.dungeon)

        self._center_camera_on_player()
        self._show_message(f"Descended to floor {self.current_floor}!", "success")
        
        # Emit floor change event
        game_events.emit(GameEventType.FLOOR_CHANGE, {
            'from_floor': old_floor,
            'to_floor': self.current_floor,
            'health_gained': health_gained
        })

    def _show_message(self, message: str, message_type: str = "info", duration: float = 3.0):
        """Show a non-intrusive message"""
        self.message = message
        self.message_type = message_type
        self.message_timer = duration
    
    def _add_floating_message(self, text: str, x: int, y: int, color: str = "ui_accent", duration: float = 2.0, animation_type: str = "float"):
        """Add a floating message at specific coordinates"""
        self.floating_messages.append({
            'text': text,
            'x': x,
            'y': y,
            'start_y': y,  # Store original Y for animation
            'color': color,
            'alpha': 1.0,
            'timer': duration,
            'duration': duration,
            'animation_type': animation_type
        })
    
    def _show_floating_damage_at_position(self, damage: int, q: int, r: int, damage_type: str):
        """Show floating damage number at specific hex coordinates"""
        world_x, world_y = HexGrid.hex_to_pixel(q, r, self.camera_x, self.camera_y)
        
        # Add some randomness to position so multiple damage numbers don't overlap
        import random
        offset_x = random.randint(-15, 15)
        offset_y = random.randint(-10, 10)
        
        text = f"-{damage}"
        if damage_type == "damage_dealt":
            # Damage dealt to enemies - show as negative (damage done)
            color = "damage_dealt"
        else:
            # Damage received by player - show as negative (health lost)
            color = "damage_received"
        
        self._add_floating_message(
            text, 
            world_x + offset_x, 
            world_y + offset_y, 
            color, 
            1.8,  # Slightly longer duration for damage
            "damage"  # Use damage animation
        )
    
    def _show_floating_message_at_position(self, text: str, q: int, r: int, color: str = "ui_accent", duration: float = 2.0):
        """Show floating message at specific hex coordinates"""
        world_x, world_y = HexGrid.hex_to_pixel(q, r, self.camera_x, self.camera_y)
        self._add_floating_message(text, world_x, world_y - 30, color, duration)
    
    def _show_floating_message_at_player(self, text: str, color: str = "ui_accent"):
        """Show floating message above player"""
        player_x, player_y = self.player.get_render_position(self.camera_x, self.camera_y)
        self._add_floating_message(text, player_x, player_y - 40, color, 2.0)
        """Show floating message above player"""
        player_x, player_y = self.player.get_render_position(self.camera_x, self.camera_y)
        self._add_floating_message(text, player_x, player_y - 40, color, 2.0)
    
    def _render_game_over_message(self):
        """Render game over message (centered, as it's critical)"""
        panel_width = 300
        panel_height = 100
        panel_x = SCREEN_WIDTH // 2 - panel_width // 2
        panel_y = SCREEN_HEIGHT // 2 - panel_height // 2
        
        self.ascii_renderer.render_ui_panel(self.screen, panel_x, panel_y, panel_width, panel_height)
        self.ascii_renderer.render_text(self.screen, "GAME OVER", panel_x + 80, panel_y + 20, "ui", "error")
        self.ascii_renderer.render_text(self.screen, "Press R to restart or ESC for menu", 
                                      panel_x + 20, panel_y + 50, "small", "ui_text")

    def _restart_game(self):
        """Restart the game"""
        self.current_floor = 1
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player = EnhancedPlayer(*self.dungeon.player_start)
        self.game_over = False
        self.message = ""
        self.message_timer = 0.0
        self.message_type = "info"
        self.floating_messages = []  # Clear floating messages
        self.enemies_defeated = 0  # Reset enemy counter
        self.hovered_hex = None
        self.camera_following = False
        self.camera_follow_timer = 0.0
        self.in_combat = False
        self.combat_log = []
        self.combat_log_timer = 0.0
        self.fog_of_war = FogOfWar()
        self.fog_of_war.update_visibility(self.player.q, self.player.r, self.dungeon)
        self.god_mode = False  # Reset god mode on restart
        self._center_camera_on_player()

    def update(self, dt: float):
        """Update game state"""
        # Start profiling
        juice_tuner.profiler.start_frame()
        
        # Use juice manager's frame clock
        juice_dt = juice_manager.tick()
        
        # Update juice effects
        juice_manager.update(juice_dt)
        
        # Update playback if active
        juice_tuner.recorder.update_playback()
        
        # Only update game logic if not paused (hit-stop effect)
        if juice_dt > 0:
            self._update_game_logic(juice_dt)
        
        # Update debug overlay
        self.debug_overlay.update(juice_tuner.profiler)
        
        # End profiling
        juice_tuner.profiler.end_frame()
    
    def _update_game_logic(self, dt: float):
        """Update game state"""
        # Update visual effects
        visual_effects.update(dt)
        
        # Update particle system
        particle_system.update(dt)
        
        # Update camera system
        self.camera_manager.update(dt, self.player.q, self.player.r)
        
        # Update camera position from camera manager
        self.camera_x, self.camera_y = self.camera_manager.get_camera_position()
        was_moving = self.player.is_moving
        self.player.update(dt)

        # Start camera follow when player finishes moving
        if was_moving and not self.player.is_moving and not self.camera_following:
            self._center_camera_on_player(animate=True)
            # Update fog of war when player stops moving
            self.fog_of_war.update_visibility(
                self.player.q, self.player.r, self.dungeon
            )
            # Process turn when player finishes moving (turn-based)
            self._process_turn()

        # Update camera animation
        if self.camera_following:
            self.camera_follow_timer += dt
            progress = min(self.camera_follow_timer / self.camera_follow_duration, 1.0)

            # Smooth easing function
            progress = progress * progress * (3.0 - 2.0 * progress)

            start_x, start_y = self.camera_start_pos
            target_x, target_y = self.camera_target_pos

            self.camera_x = start_x + (target_x - start_x) * progress
            self.camera_y = start_y + (target_y - start_y) * progress

            if progress >= 1.0:
                self.camera_following = False
                self.camera_follow_timer = 0.0

        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        
        # Update floating messages
        for floating_msg in self.floating_messages[:]:  # Copy list to avoid modification issues
            floating_msg['timer'] -= dt
            floating_msg['alpha'] = max(0, floating_msg['timer'] / floating_msg['duration'])
            
            # Different animation types
            if floating_msg['animation_type'] == 'float':
                # Standard floating upward
                floating_msg['y'] -= 30 * dt
            elif floating_msg['animation_type'] == 'damage':
                # Damage numbers: quick upward movement with slight bounce
                progress = 1.0 - (floating_msg['timer'] / floating_msg['duration'])
                if progress < 0.3:
                    # Quick upward movement
                    floating_msg['y'] = floating_msg['start_y'] - (progress * 60)
                else:
                    # Slower fade
                    floating_msg['y'] = floating_msg['start_y'] - 18 - ((progress - 0.3) * 20)
            
            if floating_msg['timer'] <= 0:
                self.floating_messages.remove(floating_msg)

        # Update combat log timer
        if self.combat_log_timer > 0:
            self.combat_log_timer -= dt
            if self.combat_log_timer <= 0:
                self.combat_log = []

    def render(self):
        """Render the entire game using juice pipeline"""
        self.juice_renderer.render_frame()
        
        # Render debug overlay on top
        self.debug_overlay.render(juice_tuner.profiler)
    
    def _draw_dungeon(self):
        """Draw dungeon layer"""
        # Render dungeon
        fog_to_use = None if self.god_mode else self.fog_of_war
        self.dungeon.render(
            self.screen,
            self.camera_x,
            self.camera_y,
            fog_to_use,
            self.ascii_renderer,
        )

        # Render movement indicators (adjacent walkable tiles)
        if not self.game_over and not self.player.is_moving:
            self._render_movement_indicators()
    
    def _draw_entities(self):
        """Draw entities layer"""
        # Render player with visual effects
        if not self.game_over:
            x, y = self.player.get_render_position(self.camera_x, self.camera_y)
            
            # Get player color with effects
            base_color = self.ascii_renderer.colors.get("player", (255, 255, 255))
            effect_color = visual_effects.get_entity_color("player", base_color)
            
            self.ascii_renderer.render_entity(self.screen, x, y, "player", effect_color)
        
        # Render floating messages (part of entities layer)
        for floating_msg in self.floating_messages:
            self.ascii_renderer.render_floating_text(
                self.screen, 
                floating_msg['text'], 
                floating_msg['x'], 
                floating_msg['y'],
                floating_msg['color'],
                floating_msg['alpha'],
                floating_msg.get('animation_type', 'float')
            )
    
    def _draw_ui(self):
        """Draw UI layer"""
        # Render UI with ASCII styling
        self.ascii_renderer.render_status_panel(self.screen, self.player, self.god_mode)

        # Render non-intrusive message panel
        if self.message:
            self.ascii_renderer.render_message_panel(self.screen, self.message, self.message_type)

        # Render combat log
        if self.combat_log:
            self.ascii_renderer.render_combat_log_panel(self.screen, self.combat_log)

        # Render game over message (this one can stay centered as it's important)
        if self.game_over:
            self._render_game_over_message()

    def _render_movement_indicators(self):
        """Render indicators for valid movement tiles"""
        neighbors = HexGrid.get_hex_neighbors(self.player.q, self.player.r)

        for q, r in neighbors:
            # In god mode, show all walkable tiles; otherwise respect fog of war
            is_visible = self.god_mode or self.fog_of_war.is_visible(q, r)
            
            if self.dungeon.is_walkable(q, r) and is_visible:
                x, y = HexGrid.hex_to_pixel(q, r, self.camera_x, self.camera_y)
                vertices = HexGrid.get_hex_vertices(x, y)

                # Check if there's an enemy here
                has_enemy = self.dungeon.has_enemy(q, r)

                # Different highlight for hovered vs normal adjacent tiles
                if self.hovered_hex == (q, r):
                    # Bright highlight for hovered tile
                    if has_enemy:
                        pygame.draw.polygon(self.screen, (255, 100, 100), vertices, 3)
                    else:
                        pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 3)
                else:
                    # Subtle highlight for other adjacent tiles
                    if has_enemy:
                        pygame.draw.polygon(self.screen, (200, 80, 80), vertices, 2)
                    else:
                        pygame.draw.polygon(self.screen, (150, 150, 150), vertices, 1)
