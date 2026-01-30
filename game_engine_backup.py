"""
ZORK-like Text Adventure Game Engine
Matrix-based design with .ini configuration
"""

import configparser
import json
import random
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class GameObject:
    """Represents any object in the game world"""
    id: str
    name: str
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    valid_verbs: Set[str] = field(default_factory=set)
    location: Optional[str] = None  # room_id or 'inventory' or object_id (container)
    state: str = "normal"
    state_turn_count: int = 0  # How many turns in current state
    
    def get_property(self, key: str, default=None):
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value):
        self.properties[key] = value
    
    def can_contain(self) -> bool:
        return self.get_property('container', False)
    
    def is_takeable(self) -> bool:
        return self.get_property('takeable', True)


@dataclass
class Room:
    """Represents a location in the game"""
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_property(self, key: str, default=None):
        return self.properties.get(key, default)


class GameEngine:
    """
    Core game engine with matrix-based verb/object/action system
    """
    
    def __init__(self, config_path: str = "config"):
        self.config_path = config_path
        self.rooms: Dict[str, Room] = {}
        self.objects: Dict[str, GameObject] = {}
        self.verbs: Dict[str, Dict[str, Any]] = {}  # verb_id -> {aliases, handler, etc}
        self.action_matrix: Dict[str, Set[str]] = {}  # object_id -> set of valid verb_ids
        self.transformations: List[Dict[str, Any]] = []
        
        self.player_location: str = ""
        self.inventory: Set[str] = set()
        self.turn_count: int = 0
        self.game_flags: Dict[str, Any] = {}
        
        self.load_all_configs()
    
    def load_all_configs(self):
        """Load all configuration from .ini files"""
        self.load_verbs()
        self.load_rooms()
        self.load_objects()
        self.load_transformations()
    
    def load_verbs(self):
        """Load verb definitions"""
        config = configparser.ConfigParser()
        config.read(f"{self.config_path}/verbs.ini")
        
        for section in config.sections():
            verb_data = dict(config[section])
            aliases = verb_data.get('aliases', '').split(',')
            aliases = [a.strip() for a in aliases if a.strip()]
            
            self.verbs[section] = {
                'name': verb_data.get('name', section),
                'aliases': aliases,
                'requires_object': verb_data.get('requires_object', 'true').lower() == 'true',
                'description': verb_data.get('description', '')
            }
    
    def load_rooms(self):
        """Load room definitions"""
        config = configparser.ConfigParser()
        config.read(f"{self.config_path}/rooms.ini")
        
        for section in config.sections():
            room_data = dict(config[section])
            
            # Parse exits
            exits = {}
            for direction in ['north', 'south', 'east', 'west', 'up', 'down']:
                if direction in room_data:
                    exits[direction] = room_data.pop(direction)
            
            # Parse properties (anything not name/description/exits)
            properties = {}
            name = room_data.pop('name', section)
            description = room_data.pop('description', '')
            
            for key, value in room_data.items():
                # Try to parse as JSON for complex types
                try:
                    properties[key] = json.loads(value)
                except:
                    properties[key] = value
            
            self.rooms[section] = Room(
                id=section,
                name=name,
                description=description,
                exits=exits,
                properties=properties
            )
    
    def load_objects(self):
        """Load object definitions and action matrix"""
        config = configparser.ConfigParser()
        config.read(f"{self.config_path}/objects.ini")
        
        for section in config.sections():
            obj_data = dict(config[section])
            
            # Parse valid verbs
            valid_verbs_str = obj_data.pop('valid_verbs', '')
            valid_verbs = set(v.strip() for v in valid_verbs_str.split(',') if v.strip())
            
            # Parse initial location
            location = obj_data.pop('location', None)
            
            # Parse properties
            properties = {}
            name = obj_data.pop('name', section)
            description = obj_data.pop('description', '')
            initial_state = obj_data.pop('state', 'normal')
            
            for key, value in obj_data.items():
                # Try to parse as JSON for booleans, numbers, etc.
                try:
                    properties[key] = json.loads(value)
                except:
                    properties[key] = value
            
            self.objects[section] = GameObject(
                id=section,
                name=name,
                description=description,
                properties=properties,
                valid_verbs=valid_verbs,
                location=location,
                state=initial_state
            )
            
            # Build action matrix
            self.action_matrix[section] = valid_verbs
    
    def load_transformations(self):
        """Load state transformation rules"""
        config = configparser.ConfigParser()
        config.read(f"{self.config_path}/transformations.ini")
        
        for section in config.sections():
            trans_data = dict(config[section])
            
            # Parse conditions
            conditions = {}
            for key in ['object_id', 'state', 'location_has_property', 'turns_required']:
                if key in trans_data:
                    if key == 'turns_required':
                        conditions[key] = int(trans_data[key])
                    else:
                        conditions[key] = trans_data[key]
            
            transformation = {
                'id': section,
                'conditions': conditions,
                'new_state': trans_data.get('new_state', ''),
                'new_object_id': trans_data.get('new_object_id', ''),
                'message': trans_data.get('message', '')
            }
            
            self.transformations.append(transformation)
    
    def start_game(self):
        """Initialize game state"""
        # Find starting room
        for room_id, room in self.rooms.items():
            if room.get_property('start', False):
                self.player_location = room_id
                break
        
        if not self.player_location and self.rooms:
            self.player_location = list(self.rooms.keys())[0]
        
        self.turn_count = 0
        return self.look()
    
    def process_turn(self):
        """Process end-of-turn effects (transformations, etc.)"""
        self.turn_count += 1
        messages = []
        
        # Update state turn counts
        for obj in self.objects.values():
            obj.state_turn_count += 1
        
        # Check transformations
        for transformation in self.transformations:
            msg = self.check_transformation(transformation)
            if msg:
                messages.append(msg)
        
        return messages
    
    def check_transformation(self, transformation: Dict[str, Any]) -> Optional[str]:
        """Check if a transformation should occur"""
        conditions = transformation['conditions']
        
        # Find matching object
        obj_id = conditions.get('object_id')
        if not obj_id or obj_id not in self.objects:
            return None
        
        obj = self.objects[obj_id]
        
        # Check state
        required_state = conditions.get('state')
        if required_state and obj.state != required_state:
            return None
        
        # Check location property
        location_prop = conditions.get('location_has_property')
        if location_prop and obj.location in self.rooms:
            room = self.rooms[obj.location]
            if not room.get_property(location_prop, False):
                return None
        
        # Check turns
        turns_required = conditions.get('turns_required', 0)
        if obj.state_turn_count < turns_required:
            return None
        
        # Apply transformation
        if transformation['new_state']:
            obj.state = transformation['new_state']
            obj.state_turn_count = 0
        
        # Create new object if specified
        if transformation['new_object_id']:
            new_obj_id = transformation['new_object_id']
            if new_obj_id in self.objects:
                # Clone the new object
                template = self.objects[new_obj_id]
                new_obj = GameObject(
                    id=obj.id,  # Keep same ID
                    name=template.name,
                    description=template.description,
                    properties=template.properties.copy(),
                    valid_verbs=template.valid_verbs.copy(),
                    location=obj.location,
                    state=template.state
                )
                self.objects[obj.id] = new_obj
        
        return transformation.get('message', '')
    
    def parse_command(self, command: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse command into verb and object(s)"""
        parts = command.lower().strip().split()
        if not parts:
            return "", None, None
        
        verb = parts[0]
        obj1 = parts[1] if len(parts) > 1 else None
        obj2 = parts[2] if len(parts) > 2 else None
        
        # Handle multi-word objects
        if len(parts) > 1:
            obj1 = ' '.join(parts[1:])
        
        return verb, obj1, obj2
    
    def find_object(self, name: str) -> Optional[GameObject]:
        """Find object by name in current room or inventory"""
        name = name.lower().strip()
        
        # Check inventory
        for obj_id in self.inventory:
            if obj_id in self.objects:
                obj = self.objects[obj_id]
                # Exact match or partial match
                if (obj.name.lower() == name or 
                    obj.id.lower() == name or
                    name in obj.name.lower()):
                    return obj
        
        # Check current room
        for obj_id, obj in self.objects.items():
            if obj.location == self.player_location:
                # Exact match or partial match
                if (obj.name.lower() == name or 
                    obj.id.lower() == name or
                    name in obj.name.lower()):
                    return obj
        
        return None
    
    def get_verb_handler(self, verb: str) -> Optional[str]:
        """Map verb to handler function"""
        verb = verb.lower()
        
        # Direct match
        if verb in self.verbs:
            return verb
        
        # Check aliases
        for verb_id, verb_data in self.verbs.items():
            if verb in verb_data['aliases']:
                return verb_id
        
        return None
    
    def can_perform_action(self, verb_id: str, obj: GameObject) -> bool:
        """Check action matrix if verb can be performed on object"""
        return verb_id in self.action_matrix.get(obj.id, set())
    
    def execute_command(self, command: str) -> str:
        """Main command execution"""
        verb, obj_name, obj2_name = self.parse_command(command)
        
        if not verb:
            return "I didn't understand that."
        
        verb_id = self.get_verb_handler(verb)
        if not verb_id:
            return f"I don't know how to '{verb}'."
        
        # Handle directional movement specially
        direction_map = {
            'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
            'u': 'up', 'd': 'down',
            'north': 'north', 'south': 'south', 'east': 'east', 
            'west': 'west', 'up': 'up', 'down': 'down'
        }
        
        if verb.lower() in direction_map:
            return self.go(direction_map[verb.lower()])
        
        # Route to appropriate handler
        handler_map = {
            'look': self.look,
            'examine': self.examine,
            'take': self.take,
            'drop': self.drop,
            'inventory': self.show_inventory,
            'go': self.go,
            'put': self.put,
            'open': self.open_obj,
            'close': self.close_obj,
            'use': self.use,
        }
        
        handler = handler_map.get(verb_id)
        if handler:
            if verb_id == 'go' and obj_name:
                return handler(obj_name)
            elif obj_name:
                obj = self.find_object(obj_name)
                if not obj:
                    return f"I don't see a {obj_name} here."
                
                if not self.can_perform_action(verb_id, obj):
                    return f"You can't {verb} the {obj.name}."
                
                if verb_id == 'put' and obj2_name:
                    return self.put(obj, obj2_name)
                else:
                    return handler(obj)
            else:
                return handler()
        
        return f"I don't know how to do that yet."
    
    def look(self, obj: Optional[GameObject] = None) -> str:
        """Look at current room or object"""
        if obj:
            return self.examine(obj)
        
        room = self.rooms.get(self.player_location)
        if not room:
            return "You are nowhere."
        
        output = [f"\n{room.name}", "=" * len(room.name), room.description]
        
        # List exits
        if room.exits:
            exits = ", ".join(room.exits.keys())
            output.append(f"\nExits: {exits}")
        
        # List objects in room
        objects_here = [obj for obj in self.objects.values() 
                       if obj.location == self.player_location]
        if objects_here:
            output.append("\nYou can see:")
            for obj in objects_here:
                state_desc = f" ({obj.state})" if obj.state != "normal" else ""
                output.append(f"  - {obj.name}{state_desc}")
        
        return "\n".join(output)
    
    def examine(self, obj: GameObject) -> str:
        """Examine an object closely"""
        state_desc = f" It appears to be {obj.state}." if obj.state != "normal" else ""
        return f"{obj.description}{state_desc}"
    
    def take(self, obj: GameObject) -> str:
        """Take an object"""
        if not obj.is_takeable():
            return f"You can't take the {obj.name}."
        
        if obj.id in self.inventory:
            return "You already have that."
        
        self.inventory.add(obj.id)
        obj.location = 'inventory'
        return f"Taken: {obj.name}"
    
    def drop(self, obj: GameObject) -> str:
        """Drop an object"""
        if obj.id not in self.inventory:
            return "You don't have that."
        
        self.inventory.remove(obj.id)
        obj.location = self.player_location
        return f"Dropped: {obj.name}"
    
    def show_inventory(self) -> str:
        """Show inventory"""
        if not self.inventory:
            return "You aren't carrying anything."
        
        items = [self.objects[obj_id].name for obj_id in self.inventory 
                if obj_id in self.objects]
        return "You are carrying:\n  - " + "\n  - ".join(items)
    
    def go(self, direction: str) -> str:
        """Move in a direction"""
        room = self.rooms.get(self.player_location)
        if not room:
            return "You can't go anywhere from here."
        
        direction = direction.lower()
        if direction not in room.exits:
            return f"You can't go {direction}."
        
        self.player_location = room.exits[direction]
        return self.look()
    
    def put(self, obj: GameObject, container_name: str) -> str:
        """Put object in container"""
        container = self.find_object(container_name)
        if not container:
            return f"I don't see a {container_name} here."
        
        if not container.can_contain():
            return f"You can't put things in the {container.name}."
        
        if obj.id not in self.inventory:
            return "You need to be holding it first."
        
        self.inventory.remove(obj.id)
        obj.location = container.id
        return f"You put the {obj.name} in the {container.name}."
    
    def open_obj(self, obj: GameObject) -> str:
        """Open a container"""
        if not obj.can_contain():
            return f"You can't open the {obj.name}."
        
        # List contents
        contents = [o for o in self.objects.values() if o.location == obj.id]
        if not contents:
            return f"The {obj.name} is empty."
        
        items = ", ".join([o.name for o in contents])
        return f"The {obj.name} contains: {items}"
    
    def close_obj(self, obj: GameObject) -> str:
        """Close a container"""
        if not obj.can_contain():
            return f"You can't close the {obj.name}."
        return f"You close the {obj.name}."
    
    def use(self, obj: GameObject) -> str:
        """Use an object"""
        # Generic use - can be extended
        return f"You're not sure how to use the {obj.name}."
    
    def save_game(self, filename: str) -> str:
        """Save game state"""
        state = {
            'player_location': self.player_location,
            'inventory': list(self.inventory),
            'turn_count': self.turn_count,
            'game_flags': self.game_flags,
            'objects': {
                obj_id: {
                    'location': obj.location,
                    'state': obj.state,
                    'state_turn_count': obj.state_turn_count,
                    'properties': obj.properties
                }
                for obj_id, obj in self.objects.items()
            }
        }
        
        with open(f"{filename}.json", 'w') as f:
            json.dump(state, f, indent=2)
        
        return f"Game saved to {filename}.json"
    
    def load_game(self, filename: str) -> str:
        """Load game state"""
        try:
            with open(f"{filename}.json", 'r') as f:
                state = json.load(f)
            
            self.player_location = state['player_location']
            self.inventory = set(state['inventory'])
            self.turn_count = state['turn_count']
            self.game_flags = state['game_flags']
            
            # Restore object states
            for obj_id, obj_state in state['objects'].items():
                if obj_id in self.objects:
                    obj = self.objects[obj_id]
                    obj.location = obj_state['location']
                    obj.state = obj_state['state']
                    obj.state_turn_count = obj_state['state_turn_count']
                    obj.properties = obj_state['properties']
            
            return f"Game loaded from {filename}.json\n\n" + self.look()
        except FileNotFoundError:
            return f"Save file {filename}.json not found."
        except Exception as e:
            return f"Error loading game: {e}"
