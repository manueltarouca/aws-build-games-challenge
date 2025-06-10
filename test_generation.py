#!/usr/bin/env python3
"""
Test the Nuclear Throne generation system
"""

try:
    from game.nuclear_throne_generator import NuclearThroneGenerator
    from game.constants import *
    
    print("Testing Nuclear Throne generation...")
    
    generator = NuclearThroneGenerator(30, 30)
    grid, start_pos = generator.generate(1)
    
    print(f"✓ Generated floor with {len(grid)} tiles")
    print(f"✓ Player start at: {start_pos}")
    
    # Count tile types
    tile_counts = {}
    for tile_type in grid.values():
        tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1
    
    print("Tile distribution:")
    for tile_type, count in tile_counts.items():
        tile_name = {
            TILE_FLOOR: "Floor",
            TILE_WALL: "Wall", 
            TILE_STAIRS_DOWN: "Stairs",
            TILE_GOLD: "Gold"
        }.get(tile_type, f"Unknown({tile_type})")
        print(f"  {tile_name}: {count}")
    
    print("\n🎮 Generation test successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
