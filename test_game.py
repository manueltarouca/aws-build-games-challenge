#!/usr/bin/env python3
"""
Quick test to verify the game loads without errors
"""

try:
    import pygame
    print("✓ Pygame imported successfully")
    
    from game.game_engine import GameEngine
    print("✓ Game engine imported successfully")
    
    from game.ascii_renderer import ASCIIRenderer
    print("✓ ASCII renderer imported successfully")
    
    from game.enemy import Enemy
    print("✓ Enemy system imported successfully")
    
    from game.fog_of_war import FogOfWar
    print("✓ Fog of war imported successfully")
    
    print("\n🎮 All game modules loaded successfully!")
    print("Run 'python main.py' to start the game")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
