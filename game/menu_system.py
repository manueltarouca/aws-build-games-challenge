"""
Menu system for the hexagonal dungeon crawler
"""

import pygame
from typing import Optional, List, Dict, Callable
from .constants import *
from .ascii_renderer import ASCIIRenderer
from .highscore_client import highscore_client

class MenuState:
    """Represents different menu states"""
    MAIN_MENU = "main_menu"
    HIGHSCORES = "highscores"
    USERNAME_INPUT = "username_input"
    GAME_OVER = "game_over"

class MenuItem:
    """A menu item with text and action"""
    def __init__(self, text: str, action: Callable, enabled: bool = True):
        self.text = text
        self.action = action
        self.enabled = enabled

class MenuSystem:
    """Handles all menu screens and navigation"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ascii_renderer = ASCIIRenderer()
        self.current_state = MenuState.MAIN_MENU
        self.selected_index = 0
        
        # Username input
        self.username_input = ""
        self.username_cursor_blink = 0.0
        
        # Highscore data
        self.highscores_data = None
        self.user_rank_data = None
        self.loading_highscores = False
        
        # Game over data
        self.game_over_stats = None
        
        # Service availability
        self.service_available = False
        self.check_service_availability()
    
    def check_service_availability(self):
        """Check if highscore service is available"""
        self.service_available = highscore_client.is_service_available()
    
    def update(self, dt: float):
        """Update menu system"""
        self.username_cursor_blink += dt
        
        # Auto-refresh highscores periodically
        if self.current_state == MenuState.HIGHSCORES and not self.loading_highscores:
            if not self.highscores_data or pygame.time.get_ticks() % 10000 < 100:
                self.load_highscores()
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle menu events, returns action or None"""
        if event.type == pygame.KEYDOWN:
            if self.current_state == MenuState.USERNAME_INPUT:
                return self._handle_username_input(event)
            else:
                return self._handle_menu_navigation(event)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_mouse_click(event.pos)
        
        return None
    
    def _handle_username_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle username input"""
        if event.key == pygame.K_RETURN:
            if self.username_input.strip():
                # Username submitted - attempt to submit any pending score
                self._attempt_score_submission()
                return "submit_username"
        elif event.key == pygame.K_ESCAPE:
            return "back_to_main"
        elif event.key == pygame.K_BACKSPACE:
            self.username_input = self.username_input[:-1]
        else:
            # Add character if printable and not too long
            if event.unicode.isprintable() and len(self.username_input) < 20:
                self.username_input += event.unicode
        
        return None
    
    def _handle_menu_navigation(self, event: pygame.event.Event) -> Optional[str]:
        """Handle menu navigation"""
        menu_items = self._get_current_menu_items()
        
        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(menu_items)
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(menu_items)
        elif event.key == pygame.K_RETURN:
            if menu_items and self.selected_index < len(menu_items):
                return menu_items[self.selected_index].action()
        elif event.key == pygame.K_ESCAPE:
            if self.current_state != MenuState.MAIN_MENU:
                return "back_to_main"
        
        return None
    
    def _handle_mouse_click(self, pos: tuple) -> Optional[str]:
        """Handle mouse clicks on menu items"""
        # Simple click detection - would need proper button bounds in real implementation
        return None
    
    def _get_current_menu_items(self) -> List[MenuItem]:
        """Get menu items for current state"""
        if self.current_state == MenuState.MAIN_MENU:
            return [
                MenuItem("Play Game", lambda: "start_game"),
                MenuItem("Highscores", lambda: self._show_highscores()),
                MenuItem("Enter Username", lambda: self._show_username_input()),
                MenuItem("Quit", lambda: "quit_game")
            ]
        
        elif self.current_state == MenuState.HIGHSCORES:
            return [
                MenuItem("Refresh", lambda: self._refresh_highscores()),
                MenuItem("Back to Main Menu", lambda: "back_to_main")
            ]
        
        elif self.current_state == MenuState.GAME_OVER:
            items = [
                MenuItem("Play Again", lambda: "start_game"),
                MenuItem("View Highscores", lambda: self._show_highscores()),
                MenuItem("Main Menu", lambda: "back_to_main")
            ]
            
            # Add username/submit options based on current state
            if not self.username_input.strip():
                items.insert(1, MenuItem("Enter Username", lambda: self._show_username_input()))
            elif self.game_over_stats and not self.game_over_stats.get('submitted', False):
                items.insert(1, MenuItem("Submit Score", lambda: self._manual_score_submission()))
            
            return items
        
        return []
    
    def _show_highscores(self) -> str:
        """Show highscores screen"""
        self.current_state = MenuState.HIGHSCORES
        self.selected_index = 0
        # Always refresh when showing highscores to ensure latest data
        self.highscores_data = None  # Clear cached data
        self.load_highscores()
        return "menu_change"
    
    def _show_username_input(self) -> str:
        """Show username input screen"""
        self.current_state = MenuState.USERNAME_INPUT
        return "menu_change"
    
    def _refresh_highscores(self) -> str:
        """Refresh highscores"""
        self.load_highscores()
        return "menu_change"
    
    def _manual_score_submission(self) -> str:
        """Manually trigger score submission"""
        self._attempt_score_submission()
        return "menu_change"
    
    def load_highscores(self):
        """Load highscores from service"""
        if not self.service_available:
            return
        
        self.loading_highscores = True
        
        def callback(result):
            self.loading_highscores = False
            if result.get('success'):
                self.highscores_data = result.get('scores', [])
            else:
                self.highscores_data = None
        
        # Load asynchronously
        import threading
        def load():
            result = highscore_client.get_highscores(10)
            callback(result)
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def submit_score(self, score: int, floor_reached: int, gold_collected: int, enemies_defeated: int):
        """Store score data and show game over screen"""
        self.game_over_stats = {
            'score': score,
            'floor_reached': floor_reached,
            'gold_collected': gold_collected,
            'enemies_defeated': enemies_defeated,
            'submitted': False  # Track if this score has been submitted
        }
        
        # Try to submit immediately if we have a username
        self._attempt_score_submission()
        
        self.current_state = MenuState.GAME_OVER
        self.selected_index = 0
    
    def _attempt_score_submission(self):
        """Attempt to submit the current game's score"""
        if not self.game_over_stats or self.game_over_stats.get('submitted', False):
            return  # No score to submit or already submitted
        
        if not self.service_available:
            print("⚠️  Highscore service unavailable - score not submitted")
            return
        
        # Use current username or "Anonymous"
        username = self.username_input.strip() or "Anonymous"
        
        print(f"🚀 Submitting score for {username}...")
        
        def callback(result):
            if result.get('success'):
                print(f"✅ Score submitted successfully: {result}")
                # Mark as submitted
                if self.game_over_stats:
                    self.game_over_stats['submitted'] = True
                
                # Load user rank after successful submission
                self.load_user_rank()
                
                # Refresh the main highscores list after a brief delay
                import threading
                import time
                def delayed_refresh():
                    time.sleep(0.5)  # Wait 500ms
                    self.load_highscores()
                
                refresh_thread = threading.Thread(target=delayed_refresh, daemon=True)
                refresh_thread.start()
            else:
                print(f"❌ Score submission failed: {result}")
        
        highscore_client.submit_score_async(
            username,
            self.game_over_stats['score'],
            self.game_over_stats['floor_reached'],
            self.game_over_stats['gold_collected'],
            self.game_over_stats['enemies_defeated'],
            callback
        )
    
    def load_user_rank(self):
        """Load user's rank"""
        if not self.username_input.strip() or not self.service_available:
            return
        
        def callback(result):
            if result.get('success'):
                self.user_rank_data = result
        
        import threading
        def load():
            result = highscore_client.get_user_rank(self.username_input.strip())
            callback(result)
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def render(self):
        """Render current menu"""
        self.screen.fill(self.ascii_renderer.colors["background"])
        
        if self.current_state == MenuState.MAIN_MENU:
            self._render_main_menu()
        elif self.current_state == MenuState.HIGHSCORES:
            self._render_highscores()
        elif self.current_state == MenuState.USERNAME_INPUT:
            self._render_username_input()
        elif self.current_state == MenuState.GAME_OVER:
            self._render_game_over()
    
    def _render_main_menu(self):
        """Render main menu"""
        # Title
        title_y = 100
        self.ascii_renderer.render_text(self.screen, "HEXAGONAL DUNGEON CRAWLER", 
                                      SCREEN_WIDTH//2 - 200, title_y, "ui", "ui_accent")
        
        # ASCII art
        ascii_art = [
            "    @ ",
            "   /|\\",
            "  # . #",
            " #  >  #",
            "#   $   #"
        ]
        
        art_y = title_y + 60
        for i, line in enumerate(ascii_art):
            self.ascii_renderer.render_text(self.screen, line, 
                                          SCREEN_WIDTH//2 - 40, art_y + i * 25, "tile", "ui_text")
        
        # Menu items
        menu_items = self._get_current_menu_items()
        menu_y = art_y + len(ascii_art) * 25 + 40
        
        for i, item in enumerate(menu_items):
            color = "ui_accent" if i == self.selected_index else "ui_text"
            prefix = "> " if i == self.selected_index else "  "
            
            self.ascii_renderer.render_text(self.screen, f"{prefix}{item.text}", 
                                          SCREEN_WIDTH//2 - 100, menu_y + i * 30, "ui", color)
        
        # Service status
        status_text = "Online" if self.service_available else "Offline"
        status_color = "ui_accent" if self.service_available else "ui_text"
        self.ascii_renderer.render_text(self.screen, f"Highscore Service: {status_text}", 
                                      10, SCREEN_HEIGHT - 30, "small", status_color)
        
        # Username display
        if self.username_input.strip():
            self.ascii_renderer.render_text(self.screen, f"Player: {self.username_input}", 
                                          10, SCREEN_HEIGHT - 60, "small", "ui_accent")
    
    def _render_highscores(self):
        """Render highscores screen"""
        # Title
        self.ascii_renderer.render_text(self.screen, "HIGHSCORES", 
                                      SCREEN_WIDTH//2 - 80, 50, "ui", "ui_accent")
        
        if self.loading_highscores:
            self.ascii_renderer.render_text(self.screen, "Loading...", 
                                          SCREEN_WIDTH//2 - 50, 150, "ui", "ui_text")
        elif not self.service_available:
            self.ascii_renderer.render_text(self.screen, "Service Unavailable", 
                                          SCREEN_WIDTH//2 - 100, 150, "ui", "ui_text")
        elif self.highscores_data:
            # Render highscore table
            y_offset = 120
            headers = ["Rank", "Player", "Score", "Floor", "Gold"]
            header_x_positions = [50, 150, 300, 400, 480]
            
            # Headers
            for i, header in enumerate(headers):
                self.ascii_renderer.render_text(self.screen, header, 
                                              header_x_positions[i], y_offset, "small", "ui_accent")
            
            y_offset += 30
            
            # Scores
            for i, score in enumerate(self.highscores_data[:10]):
                rank = i + 1
                color = "ui_accent" if rank <= 3 else "ui_text"
                
                values = [
                    f"{rank}.",
                    score['username'][:12],
                    str(score['score']),
                    str(score['floor_reached']),
                    str(score['gold_collected'])
                ]
                
                for j, value in enumerate(values):
                    self.ascii_renderer.render_text(self.screen, value, 
                                                  header_x_positions[j], y_offset, "small", color)
                
                y_offset += 25
        else:
            self.ascii_renderer.render_text(self.screen, "No scores available", 
                                          SCREEN_WIDTH//2 - 100, 150, "ui", "ui_text")
        
        # Menu navigation
        menu_items = self._get_current_menu_items()
        menu_y = SCREEN_HEIGHT - 100
        
        for i, item in enumerate(menu_items):
            color = "ui_accent" if i == self.selected_index else "ui_text"
            prefix = "> " if i == self.selected_index else "  "
            
            self.ascii_renderer.render_text(self.screen, f"{prefix}{item.text}", 
                                          50, menu_y + i * 25, "ui", color)
    
    def _render_username_input(self):
        """Render username input screen"""
        # Title
        self.ascii_renderer.render_text(self.screen, "ENTER USERNAME", 
                                      SCREEN_WIDTH//2 - 100, 200, "ui", "ui_accent")
        
        # Input field
        input_text = self.username_input
        if self.username_cursor_blink % 1.0 < 0.5:  # Blinking cursor
            input_text += "_"
        
        self.ascii_renderer.render_text(self.screen, f"Name: {input_text}", 
                                      SCREEN_WIDTH//2 - 100, 280, "ui", "ui_text")
        
        # Instructions
        instructions = [
            "Enter your name and press ENTER",
            "ESC to go back",
            "Max 20 characters"
        ]
        
        for i, instruction in enumerate(instructions):
            self.ascii_renderer.render_text(self.screen, instruction, 
                                          SCREEN_WIDTH//2 - 150, 350 + i * 25, "small", "ui_text")
    
    def _render_game_over(self):
        """Render game over screen with stats"""
        # Title
        self.ascii_renderer.render_text(self.screen, "GAME OVER", 
                                      SCREEN_WIDTH//2 - 80, 80, "ui", "ui_accent")
        
        if self.game_over_stats:
            # Stats panel
            panel_x = SCREEN_WIDTH//2 - 150
            panel_y = 140
            self.ascii_renderer.render_ui_panel(self.screen, panel_x, panel_y, 300, 200)
            
            stats_y = panel_y + 20
            stats = [
                f"Final Score: {self.game_over_stats['score']}",
                f"Floor Reached: {self.game_over_stats['floor_reached']}",
                f"Gold Collected: {self.game_over_stats['gold_collected']}",
                f"Enemies Defeated: {self.game_over_stats['enemies_defeated']}"
            ]
            
            for i, stat in enumerate(stats):
                self.ascii_renderer.render_text(self.screen, stat, 
                                              panel_x + 20, stats_y + i * 30, "ui", "ui_text")
            
            # User rank if available
            if self.user_rank_data:
                rank_text = f"Your Rank: #{self.user_rank_data['rank']}"
                self.ascii_renderer.render_text(self.screen, rank_text, 
                                              panel_x + 20, stats_y + len(stats) * 30 + 10, "ui", "ui_accent")
            
            # Submission status
            submission_y = stats_y + len(stats) * 30 + 40
            if self.game_over_stats.get('submitted', False):
                status_text = "✅ Score Submitted"
                status_color = "ui_accent"
            elif not self.service_available:
                status_text = "⚠️ Service Unavailable"
                status_color = "ui_text"
            elif not self.username_input.strip():
                status_text = "⏳ Enter Username to Submit"
                status_color = "ui_text"
            else:
                status_text = "⏳ Ready to Submit"
                status_color = "ui_text"
            
            self.ascii_renderer.render_text(self.screen, status_text, 
                                          panel_x + 20, submission_y, "small", status_color)
        
        # Menu items
        menu_items = self._get_current_menu_items()
        menu_y = 380
        
        for i, item in enumerate(menu_items):
            color = "ui_accent" if i == self.selected_index else "ui_text"
            prefix = "> " if i == self.selected_index else "  "
            
            self.ascii_renderer.render_text(self.screen, f"{prefix}{item.text}", 
                                          SCREEN_WIDTH//2 - 100, menu_y + i * 30, "ui", color)
    
    def get_username(self) -> str:
        """Get current username"""
        return self.username_input.strip() or "Anonymous"
    
    def set_username(self, username: str):
        """Set username and attempt to submit any pending score"""
        self.username_input = username[:20]
        
        # If we have an unsubmitted score from the current game, try to submit it now
        self._attempt_score_submission()
