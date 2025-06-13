#!/usr/bin/env python3
"""
Hexagonal Dungeon Crawler - Main Game Loop
"""

import pygame
import sys
from game.constants import *
from game.game_engine import GameEngine
from game.menu_system import MenuSystem, MenuState

class GameState:
    """Game state management"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"

def main():
    """Main game loop"""
    # Initialize Pygame
    pygame.init()
    
    # Create screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hexagonal Dungeon Crawler")
    
    # Game systems
    clock = pygame.time.Clock()
    menu_system = MenuSystem(screen)
    game_engine = None
    
    # Game state
    current_state = GameState.MENU
    running = True
    
    print("🎮 Hexagonal Dungeon Crawler Started!")
    print("📊 Highscore service integration enabled")
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif current_state == GameState.MENU:
                action = menu_system.handle_event(event)
                
                if action == "start_game":
                    game_engine = GameEngine(screen)
                    current_state = GameState.PLAYING
                
                elif action == "quit_game":
                    running = False
                
                elif action == "back_to_main":
                    menu_system.current_state = MenuState.MAIN_MENU
                    menu_system.selected_index = 0
                
                elif action == "submit_username":
                    # Username was entered, go back to main menu
                    menu_system.current_state = MenuState.MAIN_MENU
                    menu_system.selected_index = 0
            
            elif current_state == GameState.PLAYING:
                if game_engine:
                    game_engine.handle_event(event)
                    
                    # Check for game over
                    if game_engine.game_over:
                        # Submit score and show game over menu
                        username = menu_system.get_username()
                        menu_system.submit_score(
                            game_engine.player.gold,  # Score is gold collected
                            game_engine.current_floor,
                            game_engine.player.gold,
                            game_engine.enemies_defeated
                        )
                        current_state = GameState.MENU
                        game_engine = None
                
                # ESC to pause/menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = GameState.MENU
                    menu_system.current_state = MenuState.MAIN_MENU
                    menu_system.selected_index = 0
        
        # Update
        if current_state == GameState.MENU:
            menu_system.update(dt)
        elif current_state == GameState.PLAYING and game_engine:
            game_engine.update(dt)
        
        # Render
        if current_state == GameState.MENU:
            menu_system.render()
        elif current_state == GameState.PLAYING and game_engine:
            game_engine.render()
        
        pygame.display.flip()
    
    print("👋 Thanks for playing!")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
