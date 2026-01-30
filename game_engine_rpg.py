"""
ZORK-like Text Adventure Game Engine - RPG EDITION
Matrix-based design with .ini configuration
NOW WITH: Combat, Health, Sprites/NPCs, Multiplayer Support
"""

import configparser
import json
import random
import os
from pathlib import Path
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
    location: Optional[str] = None
    state: str = "normal"
    state_turn_count: int = 0
    
    def get_property(self, key: str, default=None):
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value):
        self.properties[key] = value
    
    def can_contain(self) -> bool:
        return self.get_property('container', False)
    
    def is_takeable(self) -> bool:
        return self.get_property('takeable', True)
    
    def is_weapon(self) -> bool:
        return self.get_property('weapon', False)
    
    def get_damage(self) -> int:
        return self.get_property('damage', 0)


@dataclass
class Sprite(GameObject):
    """Represents an NPC/enemy sprite"""
    health: int = 100
    max_health: int = 100
    damage: int = 10
    aggression: float = 0.5
    ai_behavior: str = "passive"
    inventory: Set[str] = field(default_factory=set)
    
    def is_alive(self) -> bool:
        return self.health > 0
    
    def is_hostile(self) -> bool:
        return self.aggression > 0.5


@dataclass
class Room:
    """Represents a location in the game"""
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_property(self, key: str, default=None):
        return self.properties.get(key, default)


class GameEngineRPG:
    """
    Enhanced game engine with RPG features:
    - Combat system
    - Health/damage
    - Sprite/NPC AI
    - Procedural spawning
    - Multiplayer file structure
    """
    
    def __init__(self, config_path: str = "config", player_name: str = "Player", 
                 multiplayer_root: Optional[str] = None):
        self.config_path = config_path
        self.player_name = player_name
        self.multiplayer_root = Path(multiplayer_root) if multiplayer_root else None
        
        # World data
        self.rooms: Dict[str, Room] = {}
        self.objects: Dict[str, GameObject] = {}
        self.sprites: Dict[str, Sprite] = {}  # Active sprites in world
        self.sprite_templates: Dict[str, Dict] = {}  # Templates for spawning
        self.verbs: Dict[str, Dict[str, Any]] = {}
        self.action_matrix: Dict[str, Set[str]] = {}
        self.transformations: List[Dict[str, Any]] = []
        
        # Player state
        self.player_location: str = ""
        self.inventory: Set[str] = set()
        self.player_health: int = 100
        self.player_max_health: int = 100
        self.turn_count: int = 0
        self.game_flags: Dict[str, Any] = {}
        self.in_combat: bool = False
        self.combat_target: Optional[str] = None
        
        # Stats
        self.kills: int = 0
        self.deaths: int = 0
        self.potions_consumed: int = 0
        
        self.load_all_configs()
        
        # Setup multiplayer if enabled
        if self.multiplayer_root:
            self.setup_multiplayer_files()
    
    def setup_multiplayer_files(self):
        """Create multiplayer directory structure"""
        if not self.multiplayer_root:
            return
        
        # Create directories
        (self.multiplayer_root / "world").mkdir(parents=True, exist_ok=True)
        (self.multiplayer_root / "players" / self.player_name).mkdir(parents=True, exist_ok=True)
        
        # Initialize world state if it doesn't exist
        world_state_file = self.multiplayer_root / "world" / "world_state.json"
        if not world_state_file.exists():
            with open(world_state_file, 'w') as f:
                json.dump({
                    'active_sprites': {},
                    'dynamic_objects': {},
                    'turn_count': 0
                }, f, indent=2)
    
    def load_all_configs(self):
        """Load all configuration from .ini files"""
        self.load_verbs()
        self.load_rooms()
        self.load_objects()
        self.load_sprites()
        self.load_transformations()
    
    def load_sprites(self):
        """Load sprite templates"""
        config = configparser.ConfigParser()
        sprite_file = f"{self.config_path}/sprites.ini"
        
        if not os.path.exists(sprite_file):
            return  # No sprites configured
        
        config.read(sprite_file)
        
        for section in config.sections():
            sprite_data = dict(config[section])
            
            # Parse properties
            self.sprite_templates[section] = {
                'name': sprite_data.get('name', section),
                'description': sprite_data.get('description', ''),
                'health': int(sprite_data.get('health', 50)),
                'damage': int(sprite_data.get('damage', 10)),
                'aggression': float(sprite_data.get('aggression', 0.5)),
                'ai_behavior': sprite_data.get('ai_behavior', 'passive'),
                'can_pickup': sprite_data.get('can_pickup', 'false').lower() == 'true',
                'spawn_chance': float(sprite_data.get('spawn_chance', 0.05)),
                'valid_verbs': set(v.strip() for v in sprite_data.get('valid_verbs', '').split(',') if v.strip())
            }
    
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
            
            # Parse properties
            properties = {}
            name = room_data.pop('name', section)
            description = room_data.pop('description', '')
            
            for key, value in room_data.items():
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
        self.player_health = self.player_max_health
        
        # Load player state if multiplayer
        if self.multiplayer_root:
            self.load_player_state()
        
        return self.look()
    
    def spawn_sprite(self, template_name: str, location: str) -> Optional[str]:
        """Spawn a sprite from template"""
        if template_name not in self.sprite_templates:
            return None
        
        template = self.sprite_templates[template_name]
        sprite_id = f"{template_name}_{random.randint(1000, 9999)}"
        
        # Create sprite from template
        sprite = Sprite(
            id=sprite_id,
            name=template['name'],
            description=template['description'],
            properties={
                'type': 'sprite',
                'ai_behavior': template['ai_behavior'],
                'can_pickup': template['can_pickup']
            },
            valid_verbs=template['valid_verbs'],
            location=location,
            health=template['health'],
            max_health=template['health'],
            damage=template['damage'],
            aggression=template['aggression'],
            ai_behavior=template['ai_behavior']
        )
        
        self.sprites[sprite_id] = sprite
        return sprite_id
    
    def check_spawns(self):
        """Check for random sprite and item spawns"""
        messages = []
        
        # Check sprite spawns
        for template_name, template in self.sprite_templates.items():
            if random.random() < template['spawn_chance']:
                # Spawn in random room (not player's current location initially)
                rooms = [r for r in self.rooms.keys() if r != self.player_location]
                if rooms:
                    room = random.choice(rooms)
                    sprite_id = self.spawn_sprite(template_name, room)
                    if sprite_id:
                        messages.append(f"🔮 A {template['name']} has appeared somewhere in the dungeon...")
        
        # Check potion spawns
        for obj_id, obj in self.objects.items():
            if obj.get_property('consumable') and obj.location == 'none':
                spawn_chance = obj.get_property('spawn_chance', 0)
                if spawn_chance > 0 and random.random() < spawn_chance:
                    rooms = list(self.rooms.keys())
                    obj.location = random.choice(rooms)
                    messages.append(f"✨ A {obj.name} has materialized!")
        
        return messages
    
    def process_sprite_ai(self):
        """Process AI for all sprites"""
        messages = []
        
        for sprite_id, sprite in list(self.sprites.items()):
            if not sprite.is_alive():
                continue
            
            # Sprite in player's room?
            if sprite.location == self.player_location:
                # Hostile sprite attacks
                if sprite.is_hostile() and random.random() < sprite.aggression:
                    damage = sprite.damage
                    self.player_health -= damage
                    messages.append(f"⚔️  The {sprite.name} attacks you for {damage} damage!")
                    
                    if self.player_health <= 0:
                        messages.append("💀 You have been slain!")
                        self.deaths += 1
                
                # Sprite might pick up items
                if sprite.get_property('can_pickup') and random.random() < 0.3:
                    items_here = [obj for obj in self.objects.values() 
                                if obj.location == sprite.location and obj.is_weapon()]
                    if items_here:
                        item = random.choice(items_here)
                        item.location = sprite_id  # Sprite takes it
                        sprite.inventory.add(item.id)
                        messages.append(f"👹 The {sprite.name} picks up the {item.name}!")
            else:
                # Random movement
                if random.random() < 0.2:
                    if sprite.location in self.rooms:
                        room = self.rooms[sprite.location]
                        if room.exits:
                            direction = random.choice(list(room.exits.keys()))
                            sprite.location = room.exits[direction]
        
        return messages
    
    def process_turn(self):
        """Process end-of-turn effects"""
        self.turn_count += 1
        messages = []
        
        # Health depletion over time
        if self.turn_count % 5 == 0:  # Every 5 turns
            self.player_health -= 2
            if self.player_health < 30:
                messages.append("⚠️  You're feeling weak from exhaustion...")
        
        if self.player_health <= 0:
            messages.append("💀 You have died from exhaustion! GAME OVER")
            self.deaths += 1
            return messages
        
        # Update state turn counts
        for obj in self.objects.values():
            obj.state_turn_count += 1
        
        # Check transformations
        for transformation in self.transformations:
            msg = self.check_transformation(transformation)
            if msg:
                messages.append(msg)
        
        # Check spawns
        spawn_msgs = self.check_spawns()
        messages.extend(spawn_msgs)
        
        # Process sprite AI
        ai_msgs = self.process_sprite_ai()
        messages.extend(ai_msgs)
        
        # Save player state if multiplayer
        if self.multiplayer_root:
            self.save_player_state()
        
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
        
        # Check location property (or lack thereof for ice melting)
        location_prop = conditions.get('location_has_property')
        if location_prop:
            if obj.location in self.rooms:
                room = self.rooms[obj.location]
                if not room.get_property(location_prop, False):
                    return None
        else:
            # No location property specified - check if NOT in cold room (for ice melting)
            if obj.location in self.rooms:
                room = self.rooms[obj.location]
                if room.get_property('cold', False):
                    return None  # Don't melt in cold room
        
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
                template = self.objects[new_obj_id]
                new_obj = GameObject(
                    id=obj.id,
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
        
        # Handle "attack X with Y" pattern
        if verb in ['attack', 'hit', 'strike', 'fight', 'kill'] and len(parts) >= 2:
            # Find "with" keyword
            if 'with' in parts:
                with_idx = parts.index('with')
                obj1 = ' '.join(parts[1:with_idx])
                obj2 = ' '.join(parts[with_idx+1:])
                return verb, obj1, obj2
            else:
                obj1 = ' '.join(parts[1:])
                return verb, obj1, None
        
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
                if (obj.name.lower() == name or 
                    obj.id.lower() == name or
                    name in obj.name.lower()):
                    return obj
        
        # Check current room
        for obj_id, obj in self.objects.items():
            if obj.location == self.player_location:
                if (obj.name.lower() == name or 
                    obj.id.lower() == name or
                    name in obj.name.lower()):
                    return obj
        
        return None
    
    def find_sprite(self, name: str) -> Optional[Sprite]:
        """Find sprite by name in current room"""
        name = name.lower().strip()
        
        for sprite_id, sprite in self.sprites.items():
            if sprite.location == self.player_location:
                if (sprite.name.lower() == name or
                    name in sprite.name.lower() or
                    sprite_id.lower() == name):
                    return sprite
        
        return None
    
    def get_verb_handler(self, verb: str) -> Optional[str]:
        """Map verb to handler function"""
        verb = verb.lower()
        
        if verb in self.verbs:
            return verb
        
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
            'attack': self.attack,
            'flee': self.flee,
            'health': self.check_health,
            'drink': self.drink
        }
        
        handler = handler_map.get(verb_id)
        if handler:
            if verb_id == 'go' and obj_name:
                return handler(obj_name)
            elif verb_id in ['health', 'flee']:
                return handler()
            elif obj_name:
                # Try to find object or sprite
                obj = self.find_object(obj_name)
                sprite = self.find_sprite(obj_name)
                
                if verb_id == 'attack':
                    if sprite:
                        return self.attack(sprite, obj2_name)
                    elif obj:
                        return f"You can't attack the {obj.name}."
                    else:
                        return f"I don't see a {obj_name} here."
                
                if not obj:
                    return f"I don't see a {obj_name} here."
                
                if verb_id not in ['examine', 'drink'] and not self.can_perform_action(verb_id, obj):
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
        
        # List sprites in room
        sprites_here = [s for s in self.sprites.values() 
                       if s.location == self.player_location and s.is_alive()]
        if sprites_here:
            output.append("\n🚨 ENEMIES:")
            for sprite in sprites_here:
                health_bar = f"[{'█' * (sprite.health // 10)}{'░' * ((sprite.max_health - sprite.health) // 10)}]"
                items_held = ""
                if sprite.inventory:
                    item_names = [self.objects[id].name for id in sprite.inventory if id in self.objects]
                    if item_names:
                        items_held = f" (holding: {', '.join(item_names)})"
                output.append(f"  ⚔️  {sprite.name} {health_bar} {sprite.health}/{sprite.max_health} HP{items_held}")
        
        # List objects in room
        objects_here = [obj for obj in self.objects.values() 
                       if obj.location == self.player_location]
        if objects_here:
            output.append("\nYou can see:")
            for obj in objects_here:
                state_desc = f" ({obj.state})" if obj.state != "normal" else ""
                weapon_mark = " ⚔️ " if obj.is_weapon() else "  "
                output.append(f"{weapon_mark}- {obj.name}{state_desc}")
        
        return "\n".join(output)
    
    def examine(self, obj: GameObject) -> str:
        """Examine an object closely"""
        state_desc = f" It appears to be {obj.state}." if obj.state != "normal" else ""
        weapon_info = ""
        if obj.is_weapon():
            weapon_info = f" [WEAPON: {obj.get_damage()} damage]"
        consumable_info = ""
        if obj.get_property('consumable'):
            heal = obj.get_property('health_restore', 0)
            consumable_info = f" [POTION: restores {heal} HP]"
        return f"{obj.description}{state_desc}{weapon_info}{consumable_info}"
    
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
        
        output = ["You are carrying:"]
        for obj_id in self.inventory:
            if obj_id in self.objects:
                obj = self.objects[obj_id]
                weapon_mark = "⚔️ " if obj.is_weapon() else ""
                potion_mark = "💊 " if obj.get_property('consumable') else ""
                output.append(f"  {weapon_mark}{potion_mark}{obj.name}")
        return "\n".join(output)
    
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
        return f"You're not sure how to use the {obj.name}."
    
    def drink(self, obj: GameObject) -> str:
        """Drink a potion"""
        if not obj.get_property('consumable'):
            return f"You can't drink the {obj.name}."
        
        if obj.id not in self.inventory:
            return "You need to be holding it first."
        
        # Apply healing
        heal_amount = obj.get_property('health_restore', 0)
        self.player_health = min(self.player_max_health, self.player_health + heal_amount)
        self.potions_consumed += 1
        
        # Remove potion
        self.inventory.remove(obj.id)
        obj.location = 'none'  # Consumed
        
        return f"💊 You drink the {obj.name} and restore {heal_amount} HP! (Health: {self.player_health}/{self.player_max_health})"
    
    def attack(self, target: Sprite, weapon_name: Optional[str] = None) -> str:
        """Attack a sprite"""
        if not target.is_alive():
            return f"The {target.name} is already dead."
        
        # Find weapon
        weapon = None
        if weapon_name:
            weapon = self.find_object(weapon_name)
            if not weapon or weapon.id not in self.inventory:
                return f"You don't have a {weapon_name}."
            if not weapon.is_weapon():
                return f"You can't attack with the {weapon.name}."
        else:
            # Find any weapon in inventory
            for obj_id in self.inventory:
                if obj_id in self.objects and self.objects[obj_id].is_weapon():
                    weapon = self.objects[obj_id]
                    break
        
        # Calculate damage
        base_damage = 5  # Unarmed
        if weapon:
            base_damage += weapon.get_damage()
        
        # Apply damage
        target.health -= base_damage
        
        if target.health <= 0:
            target.health = 0
            self.kills += 1
            
            # Drop sprite's inventory
            loot = []
            for item_id in target.inventory:
                if item_id in self.objects:
                    self.objects[item_id].location = self.player_location
                    loot.append(self.objects[item_id].name)
            
            loot_msg = ""
            if loot:
                loot_msg = f"\n💰 The {target.name} dropped: {', '.join(loot)}"
            
            del self.sprites[target.id]
            return f"⚔️  You attack the {target.name} with {weapon.name if weapon else 'your fists'} for {base_damage} damage!\n💀 The {target.name} has been slain!{loot_msg}"
        else:
            return f"⚔️  You attack the {target.name} with {weapon.name if weapon else 'your fists'} for {base_damage} damage! ({target.health}/{target.max_health} HP remaining)"
    
    def flee(self) -> str:
        """Flee from current room"""
        room = self.rooms.get(self.player_location)
        if not room or not room.exits:
            return "There's nowhere to run!"
        
        # Pick random exit
        direction = random.choice(list(room.exits.keys()))
        self.player_location = room.exits[direction]
        return f"🏃 You flee {direction}!\n\n{self.look()}"
    
    def check_health(self) -> str:
        """Check player health"""
        health_pct = (self.player_health / self.player_max_health) * 100
        health_bar = f"[{'█' * (self.player_health // 10)}{'░' * ((self.player_max_health - self.player_health) // 10)}]"
        
        status = "Healthy"
        if health_pct < 30:
            status = "Critical! ⚠️"
        elif health_pct < 60:
            status = "Wounded"
        
        return f"💚 Health: {health_bar} {self.player_health}/{self.player_max_health} HP ({health_pct:.0f}%) - {status}"
    
    def save_player_state(self):
        """Save player state to multiplayer files"""
        if not self.multiplayer_root:
            return
        
        player_file = self.multiplayer_root / "players" / self.player_name / "player.json"
        state = {
            'name': self.player_name,
            'health': self.player_health,
            'max_health': self.player_max_health,
            'location': self.player_location,
            'inventory': list(self.inventory),
            'turn_count': self.turn_count,
            'kills': self.kills,
            'deaths': self.deaths,
            'potions_consumed': self.potions_consumed
        }
        
        with open(player_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_player_state(self):
        """Load player state from multiplayer files"""
        if not self.multiplayer_root:
            return
        
        player_file = self.multiplayer_root / "players" / self.player_name / "player.json"
        if not player_file.exists():
            return
        
        with open(player_file, 'r') as f:
            state = json.load(f)
        
        self.player_health = state.get('health', self.player_max_health)
        self.player_max_health = state.get('max_health', 100)
        self.player_location = state.get('location', self.player_location)
        self.inventory = set(state.get('inventory', []))
        self.turn_count = state.get('turn_count', 0)
        self.kills = state.get('kills', 0)
        self.deaths = state.get('deaths', 0)
        self.potions_consumed = state.get('potions_consumed', 0)
    
    def save_game(self, filename: str) -> str:
        """Save game state"""
        state = {
            'player_name': self.player_name,
            'player_location': self.player_location,
            'player_health': self.player_health,
            'player_max_health': self.player_max_health,
            'inventory': list(self.inventory),
            'turn_count': self.turn_count,
            'game_flags': self.game_flags,
            'kills': self.kills,
            'deaths': self.deaths,
            'potions_consumed': self.potions_consumed,
            'objects': {
                obj_id: {
                    'location': obj.location,
                    'state': obj.state,
                    'state_turn_count': obj.state_turn_count,
                    'properties': obj.properties
                }
                for obj_id, obj in self.objects.items()
            },
            'sprites': {
                sprite_id: {
                    'name': sprite.name,
                    'location': sprite.location,
                    'health': sprite.health,
                    'inventory': list(sprite.inventory)
                }
                for sprite_id, sprite in self.sprites.items()
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
            
            self.player_name = state.get('player_name', 'Player')
            self.player_location = state['player_location']
            self.player_health = state.get('player_health', 100)
            self.player_max_health = state.get('player_max_health', 100)
            self.inventory = set(state['inventory'])
            self.turn_count = state['turn_count']
            self.game_flags = state['game_flags']
            self.kills = state.get('kills', 0)
            self.deaths = state.get('deaths', 0)
            self.potions_consumed = state.get('potions_consumed', 0)
            
            # Restore object states
            for obj_id, obj_state in state['objects'].items():
                if obj_id in self.objects:
                    obj = self.objects[obj_id]
                    obj.location = obj_state['location']
                    obj.state = obj_state['state']
                    obj.state_turn_count = obj_state['state_turn_count']
                    obj.properties = obj_state['properties']
            
            # Restore sprites
            self.sprites = {}
            # We'd need to restore sprites from templates here if needed
            
            return f"Game loaded from {filename}.json\n\n" + self.look()
        except FileNotFoundError:
            return f"Save file {filename}.json not found."
        except Exception as e:
            return f"Error loading game: {e}"
