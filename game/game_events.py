"""
Central event bus system for game juice effects
"""

from typing import Dict, List, Callable, Any
from enum import Enum
import time

class GameEventType(Enum):
    """All game events that can trigger juice effects"""
    # Movement events
    MOVE_START = "move_start"
    MOVE_END = "move_end"
    
    # Combat events
    ATTACK_START = "attack_start"
    ATTACK_HIT = "attack_hit"
    ATTACK_MISS = "attack_miss"
    ATTACK_CRIT = "attack_crit"
    
    # Magic/abilities
    SPELL_CAST = "spell_cast"
    
    # Items and pickups
    ITEM_PICKUP = "item_pickup"
    GOLD_PICKUP = "gold_pickup"
    
    # Damage and death
    PLAYER_HURT = "player_hurt"
    ENEMY_HURT = "enemy_hurt"
    ENEMY_DEATH = "enemy_death"
    PLAYER_DEATH = "player_death"
    
    # Level progression
    FLOOR_CHANGE = "floor_change"
    LEVEL_UP = "level_up"
    
    # UI events
    MENU_SELECT = "menu_select"
    BUTTON_PRESS = "button_press"

class GameEvent:
    """Individual game event with data"""
    
    def __init__(self, event_type: GameEventType, data: Dict[str, Any] = None):
        self.type = event_type
        self.data = data or {}
        self.timestamp = time.time()
    
    def get(self, key: str, default=None):
        """Get data value with default"""
        return self.data.get(key, default)

class EventBus:
    """Central publish/subscribe event system"""
    
    def __init__(self):
        self.listeners: Dict[GameEventType, List[Callable]] = {}
        self.event_history: List[GameEvent] = []
        self.max_history = 100  # Keep last 100 events for debugging
        
    def subscribe(self, event_type: GameEventType, callback: Callable[[GameEvent], None]):
        """Subscribe to an event type"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: GameEventType, callback: Callable[[GameEvent], None]):
        """Unsubscribe from an event type"""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(callback)
            except ValueError:
                pass  # Callback wasn't subscribed
    
    def emit(self, event_type: GameEventType, data: Dict[str, Any] = None):
        """Emit an event to all subscribers"""
        event = GameEvent(event_type, data)
        
        # Add to history for debugging
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify all listeners
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback for {event_type}: {e}")
    
    def get_recent_events(self, count: int = 10) -> List[GameEvent]:
        """Get recent events for debugging"""
        return self.event_history[-count:]
    
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()

# Global event bus instance
game_events = EventBus()
