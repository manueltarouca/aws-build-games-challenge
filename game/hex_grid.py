"""
Hexagonal grid utilities and calculations
"""

import math
from typing import Tuple, List
from .constants import HEX_RADIUS, HEX_HEIGHT, HEX_WIDTH

class HexGrid:
    """Utility class for hexagonal grid calculations"""
    
    @staticmethod
    def hex_to_pixel(q: int, r: int, offset_x: int = 0, offset_y: int = 0) -> Tuple[int, int]:
        """Convert hex coordinates (q, r) to pixel coordinates"""
        x = HEX_RADIUS * (3/2 * q) + offset_x
        y = HEX_RADIUS * (math.sqrt(3)/2 * q + math.sqrt(3) * r) + offset_y
        return int(x), int(y)
    
    @staticmethod
    def pixel_to_hex(x: int, y: int, offset_x: int = 0, offset_y: int = 0) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates (q, r)"""
        x -= offset_x
        y -= offset_y
        
        q = (2/3 * x) / HEX_RADIUS
        r = (-1/3 * x + math.sqrt(3)/3 * y) / HEX_RADIUS
        
        return HexGrid.hex_round(q, r)
    
    @staticmethod
    def hex_round(q: float, r: float) -> Tuple[int, int]:
        """Round fractional hex coordinates to nearest hex"""
        s = -q - r
        
        rq = round(q)
        rr = round(r)
        rs = round(s)
        
        q_diff = abs(rq - q)
        r_diff = abs(rr - r)
        s_diff = abs(rs - s)
        
        if q_diff > r_diff and q_diff > s_diff:
            rq = -rr - rs
        elif r_diff > s_diff:
            rr = -rq - rs
        
        return rq, rr
    
    @staticmethod
    def get_hex_neighbors(q: int, r: int) -> List[Tuple[int, int]]:
        """Get the 6 neighboring hex coordinates"""
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]
        return [(q + dq, r + dr) for dq, dr in directions]
    
    @staticmethod
    def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        """Calculate distance between two hex coordinates"""
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2
    
    @staticmethod
    def hex_round(q: float, r: float) -> Tuple[int, int]:
        """Round fractional hex coordinates to nearest hex"""
        s = -q - r
        
        rq = round(q)
        rr = round(r)
        rs = round(s)
        
        q_diff = abs(rq - q)
        r_diff = abs(rr - r)
        s_diff = abs(rs - s)
        
        if q_diff > r_diff and q_diff > s_diff:
            rq = -rr - rs
        elif r_diff > s_diff:
            rr = -rq - rs
        
        return rq, rr
    
    @staticmethod
    def get_hex_vertices(center_x: int, center_y: int) -> List[Tuple[int, int]]:
        """Get the 6 vertices of a hexagon centered at (center_x, center_y)"""
        vertices = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = center_x + HEX_RADIUS * math.cos(angle)
            y = center_y + HEX_RADIUS * math.sin(angle)
            vertices.append((int(x), int(y)))
        return vertices
