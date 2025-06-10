"""
Nuclear Throne-style procedural dungeon generation using random walkers (FloorMakers)
"""

import random
from typing import List, Tuple, Set, Dict
from .constants import *
from .hex_grid import HexGrid

class FloorMaker:
    """A random walker that carves out floors and rooms"""
    
    def __init__(self, q: int, r: int, direction: int, area_type: str = "dungeon"):
        self.q = q
        self.r = r
        self.direction = direction  # 0-5 for hex directions
        self.alive = True
        self.steps_taken = 0
        self.area_type = area_type
        
        # Area-specific probabilities
        self.area_configs = {
            "dungeon": {
                "turn_chance": 0.15,      # Chance to turn each step
                "u_turn_chance": 0.05,    # Chance for 180° turn
                "room_chance": 0.08,      # Chance to carve room
                "split_chance": 0.03,     # Chance to spawn new walker
                "room_size": (2, 3),      # Min/max room radius
            },
            "caverns": {
                "turn_chance": 0.25,      # More winding
                "u_turn_chance": 0.12,    # More u-turns
                "room_chance": 0.15,      # More rooms
                "split_chance": 0.08,     # More branching
                "room_size": (2, 4),      # Larger rooms
            },
            "corridors": {
                "turn_chance": 0.08,      # Straighter paths
                "u_turn_chance": 0.02,    # Rare u-turns
                "room_chance": 0.04,      # Fewer rooms
                "split_chance": 0.02,     # Less branching
                "room_size": (1, 2),      # Smaller rooms
            }
        }
        
        self.config = self.area_configs.get(area_type, self.area_configs["dungeon"])
    
    def step(self, grid: Dict[Tuple[int, int], int], active_walkers: int) -> List['FloorMaker']:
        """Take one step and return any new walkers spawned"""
        if not self.alive:
            return []
        
        new_walkers = []
        
        # Move forward in current direction
        neighbors = HexGrid.get_hex_neighbors(self.q, self.r)
        if self.direction < len(neighbors):
            self.q, self.r = neighbors[self.direction]
            
            # Carve floor tile
            grid[(self.q, self.r)] = TILE_FLOOR
            self.steps_taken += 1
            
            # Decide on actions this step
            actions = self._decide_actions(active_walkers)
            
            # Execute actions
            if "turn" in actions:
                self._turn(actions["turn"])
            
            if "room" in actions:
                self._carve_room(grid, actions["room"])
            
            if "split" in actions:
                new_walker = self._spawn_walker()
                if new_walker:
                    new_walkers.append(new_walker)
            
            if "die" in actions:
                self.alive = False
        
        return new_walkers
    
    def _decide_actions(self, active_walkers: int) -> Dict[str, any]:
        """Decide what actions to take this step"""
        actions = {}
        
        # Turning decision
        if random.random() < self.config["turn_chance"]:
            if random.random() < self.config["u_turn_chance"]:
                actions["turn"] = "u_turn"  # 180°
            else:
                actions["turn"] = "turn"    # ±90°
        
        # Room carving decision
        if random.random() < self.config["room_chance"]:
            room_size = random.randint(*self.config["room_size"])
            actions["room"] = room_size
        
        # Splitting decision (more likely with fewer active walkers)
        split_chance = self.config["split_chance"]
        if active_walkers < 3:  # Encourage splitting when few walkers
            split_chance *= 2
        elif active_walkers > 6:  # Discourage when many walkers
            split_chance *= 0.3
        
        if random.random() < split_chance:
            actions["split"] = True
        
        # Death decision (more likely with many walkers or long life)
        death_chance = 0.001 + (active_walkers - 1) * 0.002 + self.steps_taken * 0.0001
        if random.random() < death_chance:
            actions["die"] = True
        
        return actions
    
    def _turn(self, turn_type: str):
        """Change direction"""
        if turn_type == "u_turn":
            # 180° turn
            self.direction = (self.direction + 3) % 6
        else:
            # ±90° turn
            turn_amount = random.choice([-1, 1])  # Left or right
            self.direction = (self.direction + turn_amount) % 6
    
    def _carve_room(self, grid: Dict[Tuple[int, int], int], room_size: int):
        """Carve out a room around current position"""
        # Get all tiles within room_size distance
        for distance in range(1, room_size + 1):
            tiles_at_distance = self._get_tiles_at_distance(self.q, self.r, distance)
            for tile_q, tile_r in tiles_at_distance:
                grid[(tile_q, tile_r)] = TILE_FLOOR
    
    def _get_tiles_at_distance(self, center_q: int, center_r: int, distance: int) -> Set[Tuple[int, int]]:
        """Get all tiles at a specific distance from center (hex ring)"""
        tiles = set()
        
        if distance == 0:
            return {(center_q, center_r)}
        
        # Start at one corner of the ring
        q, r = center_q - distance, center_r
        
        # Walk around the ring
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        
        for direction in directions:
            dq, dr = direction
            for _ in range(distance):
                tiles.add((q, r))
                q += dq
                r += dr
        
        return tiles
    
    def _spawn_walker(self) -> 'FloorMaker':
        """Spawn a new walker at current position"""
        # New walker goes in a different direction
        new_direction = (self.direction + random.choice([-2, -1, 1, 2])) % 6
        return FloorMaker(self.q, self.r, new_direction, self.area_type)

class NuclearThroneGenerator:
    """Nuclear Throne-style dungeon generator"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid_bounds = self._calculate_bounds()
    
    def _calculate_bounds(self) -> Tuple[int, int, int, int]:
        """Calculate the bounds of the hex grid"""
        # Convert grid size to approximate hex bounds
        min_q = -self.width // 2
        max_q = self.width // 2
        min_r = -self.height // 2
        max_r = self.height // 2
        return min_q, max_q, min_r, max_r
    
    def generate(self, floor_number: int) -> Dict[Tuple[int, int], int]:
        """Generate a dungeon floor using Nuclear Throne algorithm"""
        # Initialize grid with walls
        grid = {}
        min_q, max_q, min_r, max_r = self.grid_bounds
        
        # Fill with walls initially (we'll only track floor tiles)
        # Walls are implicit (any tile not in grid is a wall)
        
        # Determine area type based on floor
        area_type = self._get_area_type(floor_number)
        
        # Calculate target floor count
        base_tiles = 80
        target_floor_count = base_tiles + floor_number * 15
        
        # Start with one FloorMaker at center
        start_q, start_r = 0, 0
        initial_direction = random.randint(0, 5)
        
        walkers = [FloorMaker(start_q, start_r, initial_direction, area_type)]
        grid[(start_q, start_r)] = TILE_FLOOR  # Player start
        
        floor_count = 1
        generation_steps = 0
        max_steps = target_floor_count * 3  # Safety limit
        
        # Main generation loop
        while floor_count < target_floor_count and walkers and generation_steps < max_steps:
            generation_steps += 1
            new_walkers = []
            
            # Process each walker
            for walker in walkers[:]:  # Copy list to avoid modification issues
                if walker.alive:
                    # Check bounds
                    if not self._in_bounds(walker.q, walker.r):
                        walker.alive = False
                        continue
                    
                    # Take step
                    spawned = walker.step(grid, len(walkers))
                    new_walkers.extend(spawned)
                    
                    # Count new floor tiles
                    current_floor_count = len([t for t in grid.values() if t == TILE_FLOOR])
                    floor_count = current_floor_count
            
            # Add new walkers
            walkers.extend(new_walkers)
            
            # Remove dead walkers
            walkers = [w for w in walkers if w.alive]
            
            # Limit walker count
            if len(walkers) > 8:
                # Kill oldest walkers
                walkers.sort(key=lambda w: w.steps_taken, reverse=True)
                for walker in walkers[6:]:
                    walker.alive = False
                walkers = walkers[:6]
        
        # Final cleanup - kill remaining walkers after one last step
        for walker in walkers:
            if walker.alive and self._in_bounds(walker.q, walker.r):
                neighbors = HexGrid.get_hex_neighbors(walker.q, walker.r)
                if walker.direction < len(neighbors):
                    final_q, final_r = neighbors[walker.direction]
                    if self._in_bounds(final_q, final_r):
                        grid[(final_q, final_r)] = TILE_FLOOR
        
        # Post-process: add special tiles and walls
        self._place_special_tiles(grid, start_q, start_r, floor_number)
        self._add_enclosing_walls(grid)
        
        return grid, (start_q, start_r)
    
    def _get_area_type(self, floor_number: int) -> str:
        """Determine area type based on floor number"""
        if floor_number <= 2:
            return "dungeon"
        elif floor_number <= 5:
            return "corridors"
        else:
            return "caverns"
    
    def _in_bounds(self, q: int, r: int) -> bool:
        """Check if coordinates are within grid bounds"""
        min_q, max_q, min_r, max_r = self.grid_bounds
        return min_q <= q <= max_q and min_r <= r <= max_r
    
    def _place_special_tiles(self, grid: Dict[Tuple[int, int], int], start_q: int, start_r: int, floor_number: int):
        """Place stairs, gold, and other special tiles"""
        floor_tiles = [(q, r) for (q, r), tile_type in grid.items() if tile_type == TILE_FLOOR]
        
        if not floor_tiles:
            return
        
        # Remove start position from available tiles
        available_tiles = [(q, r) for (q, r) in floor_tiles if (q, r) != (start_q, start_r)]
        
        if not available_tiles:
            return
        
        # Place stairs (farthest from start)
        stairs_candidates = sorted(available_tiles, 
                                 key=lambda pos: HexGrid.hex_distance(pos[0], pos[1], start_q, start_r),
                                 reverse=True)
        
        if stairs_candidates:
            stairs_pos = stairs_candidates[0]
            grid[stairs_pos] = TILE_STAIRS_DOWN
            available_tiles.remove(stairs_pos)
        
        # Place gold (scattered around, more on higher floors)
        num_gold = random.randint(3, 5 + floor_number)
        gold_positions = random.sample(available_tiles, min(num_gold, len(available_tiles)))
        
        for pos in gold_positions:
            grid[pos] = TILE_GOLD
            available_tiles.remove(pos)
    
    def _add_enclosing_walls(self, grid: Dict[Tuple[int, int], int]):
        """Add walls around all floor tiles to enclose the space"""
        floor_tiles = [(q, r) for (q, r), tile_type in grid.items() if tile_type == TILE_FLOOR]
        wall_positions = set()
        
        # For each floor tile, check all neighbors
        for floor_q, floor_r in floor_tiles:
            neighbors = HexGrid.get_hex_neighbors(floor_q, floor_r)
            for neighbor_q, neighbor_r in neighbors:
                # If neighbor is not a floor tile and within bounds, make it a wall
                if (neighbor_q, neighbor_r) not in grid and self._in_bounds(neighbor_q, neighbor_r):
                    wall_positions.add((neighbor_q, neighbor_r))
        
        # Add all wall positions to grid
        for wall_pos in wall_positions:
            grid[wall_pos] = TILE_WALL
