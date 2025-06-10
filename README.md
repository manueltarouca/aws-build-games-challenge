# Hexagonal Dungeon Crawler

A turn-based dungeon crawler game built with PyGame featuring hexagonal grid movement and classic ASCII-style graphics.

## Features

- **Hexagonal Grid Movement**: Move in 6 directions using click-based controls
- **Nuclear Throne-Style Generation**: Organic dungeon layouts created by random walkers
- **Turn-Based Combat System**: Fight different enemy types with strategic combat
- **Enemy Variety**: Goblins, Orcs, Skeletons, and Trolls with different stats
- **Progressive Difficulty**: Higher floors have stronger enemies and better rewards
- **Health & Defense System**: Take and deal damage based on attack and defense stats
- **Gold Collection**: Collect gold from defeated enemies and treasure
- **Multi-Floor Progression**: Descend deeper into the dungeon via stairs
- **Enemy AI**: Enemies wander autonomously and chase the player when detected
- **Fog of War**: Explore the dungeon gradually with limited vision and memory
- **Retro ASCII Graphics**: Classic dungeon crawler aesthetics with polished presentation

## Controls

- **Movement**: Click on adjacent highlighted hexagonal tiles to move
- **Restart**: Click anywhere or press R when game over
- **God Mode**: Press G to toggle fog of war on/off (for debugging/exploration)
- **Visual Feedback**: Adjacent walkable tiles are highlighted with white borders
- **Hover Effect**: Tiles glow brighter when you hover over them

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## Game Elements

- **Gray Hexagons**: Floor tiles (walkable)
- **Dark Gray Hexagons**: Walls (impassable)
- **Blue Hexagons**: Stairs down to next floor
- **Gold Hexagons**: Gold to collect
- **Red Hexagons**: Enemies (fight automatically when stepped on)
- **Purple Circle**: Your player character

## Enemy Types

- **Goblins** (Red): Weak but common enemies (20 HP, 8 ATK, 2 DEF)
- **Skeletons** (Gray): Fast but fragile (15 HP, 10 ATK, 1 DEF)
- **Orcs** (Dark Red): Balanced fighters (35 HP, 12 ATK, 4 DEF)
- **Trolls** (Brown): Powerful late-game enemies (60 HP, 18 ATK, 8 DEF)

## Enemy Behavior

- **Wandering**: Enemies move randomly when not aware of the player
- **Detection**: Each enemy type has different vision ranges
- **Chasing**: Enemies will pursue the player when detected
- **Different Speeds**: Each enemy type moves at different intervals
  - Skeletons: Fast (1.5s between moves)
  - Goblins: Medium (2.5s between moves)  
  - Orcs: Slow (3.0s between moves)
  - Trolls: Very slow (4.0s between moves)

## Procedural Generation

The game uses a **Nuclear Throne-inspired** generation system:

- **Random Walkers**: "FloorMakers" carve out organic dungeon layouts
- **Dynamic Behavior**: Walkers can turn, split, carve rooms, and die based on probabilities
- **Area Types**: Different floor types (Dungeon, Corridors, Caverns) with unique characteristics
- **Organic Layouts**: No rigid room-and-corridor system - naturally flowing spaces
- **Progressive Complexity**: Deeper floors use different generation parameters

### Generation Process:
1. **Floor Carving**: Walkers move through the grid, converting walls to floors
2. **Room Creation**: Walkers occasionally carve out larger open areas
3. **Corridor Splitting**: New walkers spawn to create branching paths
4. **Smart Termination**: Process ends when target floor count is reached
5. **Item Placement**: Stairs placed far from start, gold scattered throughout

## Gameplay Tips

- Collect gold to increase your score
- Avoid enemies when possible, as they deal damage
- Your health increases when you go to the next floor
- Higher floors have more enemies but also more gold
- Plan your route carefully in the hexagonal grid

## Game Architecture

The game is built with a modular architecture:

- `main.py` - Entry point and main game loop
- `game/game_engine.py` - Core game logic and state management
- `game/player.py` - Player character with movement and stats
- `game/dungeon.py` - Procedural dungeon generation
- `game/hex_grid.py` - Hexagonal grid mathematics and utilities
- `game/constants.py` - Game configuration and constants

## Future Enhancements

- Different enemy types with varying difficulty
- Items and equipment system
- Magic spells or special abilities
- Boss fights on certain floors
- Save/load game functionality
- Sound effects and music
- Improved graphics and animations
# aws-build-games-challenge
