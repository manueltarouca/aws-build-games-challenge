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


class GameEngine:
    """Main game engine class"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # ASCII renderer for retro styling
        self.ascii_renderer = ASCIIRenderer()

        # Game state
        self.current_floor = 1
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player = Player(*self.dungeon.player_start)
        self.message = ""
        self.message_timer = 0.0
        self.game_over = False

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
        """Center the camera on the player"""
        player_pixel_x, player_pixel_y = HexGrid.hex_to_pixel(
            self.player.q, self.player.r, 0, 0
        )

        target_camera_x = SCREEN_WIDTH // 2 - player_pixel_x
        target_camera_y = SCREEN_HEIGHT // 2 - player_pixel_y

        if animate and not self.camera_following:
            # Start camera animation
            self.camera_start_pos = (self.camera_x, self.camera_y)
            self.camera_target_pos = (target_camera_x, target_camera_y)
            self.camera_following = True
            self.camera_follow_timer = 0.0
        else:
            # Immediate camera positioning
            self.camera_x = target_camera_x
            self.camera_y = target_camera_y

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
                    self._show_message("God Mode: ON (Fog of War disabled)")
                else:
                    self._show_message("God Mode: OFF (Fog of War enabled)")
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
            # Move player
            self.player.move_to(target_q, target_r, self.camera_x, self.camera_y)

            # Interact with tile
            message = self.dungeon.interact_with_tile(target_q, target_r, self.player)

            if message == "enemy":
                self._start_combat(target_q, target_r)
            elif message == "stairs_down":
                self._go_to_next_floor()
            elif message:
                self._show_message(message)

            # Check if player died
            if self.player.health <= 0:
                self.game_over = True
                self._show_message("You died! Press R to restart.")

            # Start camera follow animation after player starts moving
            # We'll trigger this in the update loop when player finishes moving

    def _start_combat(self, enemy_q: int, enemy_r: int):
        """Start combat with enemy at position"""
        enemy = self.dungeon.get_enemy(enemy_q, enemy_r)
        if enemy and enemy.alive:
            self.in_combat = True

            # Run combat
            combat_result = CombatSystem.initiate_combat(self.player, enemy)
            self.combat_log = combat_result["log"]
            self.combat_log_timer = 5.0  # Show combat log for 5 seconds

            if combat_result["player_died"]:
                self.game_over = True
                self._show_message("You died in combat! Press R to restart.")
            elif combat_result["player_won"]:
                # Remove defeated enemy
                del self.dungeon.enemies[(enemy_q, enemy_r)]

            self.in_combat = False

    def _process_turn(self):
        """Process a game turn after player moves"""
        if not self.game_over and not self.in_combat:
            # Update all enemies (turn-based)
            self.dungeon.process_enemy_turns(self.player.q, self.player.r)

    def _go_to_next_floor(self):
        """Move to the next dungeon floor"""
        self.current_floor += 1
        self.player.go_to_next_floor()

        # Generate new dungeon
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player.q, self.player.r = self.dungeon.player_start

        # Reset fog of war for new floor
        self.fog_of_war = FogOfWar()
        self.fog_of_war.update_visibility(self.player.q, self.player.r, self.dungeon)

        self._center_camera_on_player()
        self._show_message(f"Descended to floor {self.current_floor}!")

    def _show_message(self, message: str):
        """Show a temporary message"""
        self.message = message
        self.message_timer = 3.0  # Show for 3 seconds

    def _restart_game(self):
        """Restart the game"""
        self.current_floor = 1
        self.dungeon = Dungeon(GRID_WIDTH, GRID_HEIGHT, self.current_floor)
        self.player = Player(*self.dungeon.player_start)
        self.game_over = False
        self.message = ""
        self.message_timer = 0.0
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

        # Update combat log timer
        if self.combat_log_timer > 0:
            self.combat_log_timer -= dt
            if self.combat_log_timer <= 0:
                self.combat_log = []

    def render(self):
        """Render the entire game"""
        # Clear screen with retro background
        self.screen.fill(self.ascii_renderer.colors["background"])

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

        # Render player
        if not self.game_over:
            x, y = self.player.get_render_position(self.camera_x, self.camera_y)
            self.ascii_renderer.render_entity(self.screen, x, y, "player")

        # Render UI with ASCII styling
        self.ascii_renderer.render_status_panel(self.screen, self.player, self.god_mode)

        # Render combat log
        if self.combat_log:
            self.ascii_renderer.render_combat_log_panel(self.screen, self.combat_log)

        # Render messages
        if self.message:
            self._render_message()

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

    def _render_message(self):
        """Render temporary messages"""
        if self.game_over:
            # Game over message
            panel_width = 300
            panel_height = 100
            panel_x = SCREEN_WIDTH // 2 - panel_width // 2
            panel_y = SCREEN_HEIGHT // 2 - panel_height // 2

            self.ascii_renderer.render_ui_panel(
                self.screen, panel_x, panel_y, panel_width, panel_height
            )
            self.ascii_renderer.render_text(
                self.screen, "GAME OVER", panel_x + 80, panel_y + 20, "ui", "ui_accent"
            )
            self.ascii_renderer.render_text(
                self.screen, self.message, panel_x + 20, panel_y + 50, "small"
            )
        else:
            # Regular message
            panel_width = len(self.message) * 12 + 40
            panel_height = 60
            panel_x = SCREEN_WIDTH // 2 - panel_width // 2
            panel_y = SCREEN_HEIGHT // 2 - panel_height // 2

            self.ascii_renderer.render_ui_panel(
                self.screen, panel_x, panel_y, panel_width, panel_height
            )
            self.ascii_renderer.render_text(
                self.screen, self.message, panel_x + 20, panel_y + 20, "ui"
            )
