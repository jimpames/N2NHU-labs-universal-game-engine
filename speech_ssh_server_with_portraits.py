#!/usr/bin/env python3
"""
ZORK RPG - Enhanced Server with CHARACTER PORTRAITS
Now shows player avatar with inventory when they type 'i' or 'inventory'!
"""

import asyncio
import asyncssh
import sys
from pathlib import Path
from game_engine_rpg import GameEngineRPG
from typing import Dict, Optional
import json
import requests
import base64
import configparser
import re
from PIL import Image
from io import BytesIO


class StableDiffusionLoadBalancer:
    """Load balancer for multiple SD servers"""
    
    def __init__(self, config_path: str = "stablediffusion.ini"):
        self.config_path = config_path
        self.servers = []
        self.current_index = 0
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.settings = {}
        
        self.load_config()
    
    def load_config(self):
        """Load SD server configuration"""
        if not Path(self.config_path).exists():
            print("⚠️  No stablediffusion.ini found - SD disabled")
            return
        
        config = configparser.ConfigParser()
        config.read(self.config_path)
        
        # Load servers
        for section in config.sections():
            if section.startswith('SD'):
                if config.getboolean(section, 'enabled', fallback=True):
                    server = {
                        'name': section,
                        'host': config.get(section, 'host'),
                        'port': config.getint(section, 'port', fallback=7860),
                        'weight': config.getint(section, 'weight', fallback=1),
                        'timeout': config.getint(section, 'timeout', fallback=60),
                        'url': f"http://{config.get(section, 'host')}:{config.getint(section, 'port', fallback=7860)}"
                    }
                    self.servers.append(server)
        
        # Load settings
        if 'settings' in config.sections():
            self.settings = {
                'steps': config.getint('settings', 'default_steps', fallback=20),
                'width': config.getint('settings', 'default_width', fallback=512),
                'height': config.getint('settings', 'default_height', fallback=512),
                'cfg': config.getfloat('settings', 'default_cfg', fallback=7.0),
                'sampler': config.get('settings', 'default_sampler', fallback='DPM++ 2M'),
                'cache_images': config.getboolean('settings', 'cache_images', fallback=True),
                'image_format': config.get('settings', 'image_format', fallback='jpg'),
                'image_quality': config.getint('settings', 'image_quality', fallback=85)
            }
        
        # Load prompt styles
        if 'prompt_style' in config.sections():
            self.settings['scene_suffix'] = config.get('prompt_style', 'scene_suffix', 
                fallback='fantasy RPG game environment, detailed, atmospheric lighting')
            self.settings['negative_prompt'] = config.get('prompt_style', 'negative_prompt',
                fallback='blurry, low quality, distorted')
        
        if self.servers:
            print(f"🎨 Loaded {len(self.servers)} SD servers for load balancing")
            for server in self.servers:
                print(f"   • {server['name']}: {server['url']}")
    
    def get_next_server(self) -> Optional[Dict]:
        """Round-robin server selection"""
        if not self.servers:
            return None
        
        server = self.servers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.servers)
        return server
    
    def sanitize_look_to_prompt(self, look_output: str) -> str:
        """Convert LOOK output to SD prompt"""
        lines = look_output.split('\n')
        clean_lines = []
        
        skip_markers = ['PLAYERS HERE:', '👥', '💬', 'TELL', '>', '===', '---', 'ENEMIES:', '🚨', 'Exits:', 'You can see:']
        
        for line in lines:
            if any(marker in line for marker in skip_markers):
                continue
            
            if re.match(r'^[\s\-=_│║╔╗╚╝]+$', line):
                continue
            
            if not line.strip():
                continue
            
            clean_lines.append(line.strip())
        
        description = ' '.join(clean_lines)
        description = re.sub(r'[⚔️🔥💀👤🕊️⚠️💬💨💋✅❌📊💰🚨🌟👋🎨🎮█▒]', '', description)
        
        prompt = f"{description}, {self.settings.get('scene_suffix', '')}"
        
        return prompt.strip()
    
    def generate_image(self, prompt: str, cache_key: str = None) -> Optional[bytes]:
        """Generate image using load-balanced SD servers"""
        
        # Check cache first
        if cache_key and self.settings.get('cache_images', True):
            cache_path = self.cache_dir / f"{cache_key}.jpg"
            if cache_path.exists():
                print(f"🎨 Using cached image: {cache_key}")
                with open(cache_path, 'rb') as f:
                    return f.read()
        
        # Try servers in round-robin
        attempts = 0
        max_attempts = len(self.servers) if self.servers else 0
        
        while attempts < max_attempts:
            server = self.get_next_server()
            if not server:
                break
            
            print(f"🎨 Generating image via {server['name']} ({server['url']})")
            print(f"   Prompt: {prompt[:80]}...")
            
            try:
                response = requests.post(
                    f"{server['url']}/sdapi/v1/txt2img",
                    json={
                        "prompt": prompt,
                        "negative_prompt": self.settings.get('negative_prompt', ''),
                        "steps": self.settings.get('steps', 20),
                        "width": self.settings.get('width', 512),
                        "height": self.settings.get('height', 512),
                        "cfg_scale": self.settings.get('cfg', 7),
                        "sampler_name": self.settings.get('sampler', 'DPM++ 2M')
                    },
                    timeout=server['timeout']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    png_data = base64.b64decode(result['images'][0])
                    
                    if self.settings.get('image_format') == 'jpg':
                        img = Image.open(BytesIO(png_data))
                        jpg_buffer = BytesIO()
                        img.convert('RGB').save(jpg_buffer, 'JPEG', 
                                               quality=self.settings.get('image_quality', 85))
                        image_data = jpg_buffer.getvalue()
                    else:
                        image_data = png_data
                    
                    if cache_key and self.settings.get('cache_images', True):
                        cache_path = self.cache_dir / f"{cache_key}.jpg"
                        with open(cache_path, 'wb') as f:
                            f.write(image_data)
                        print(f"✅ Image cached: {cache_key}")
                    
                    print(f"✅ Image generated successfully!")
                    return image_data
                else:
                    print(f"❌ SD server returned {response.status_code}")
                    attempts += 1
                    
            except Exception as e:
                print(f"❌ SD generation failed on {server['name']}: {e}")
                attempts += 1
        
        print("❌ All SD servers failed or unavailable")
        return None


class PlayerSession:
    """Represents one connected player"""
    def __init__(self, player_name: str, process):
        self.player_name = player_name
        self.process = process
        self.location = "entrance_hall"
        self.health = 100
        self.inventory = set()
        self.last_message = ""
        self.supports_images = True
    
    async def send(self, message: str):
        """Send message to this player"""
        try:
            self.process.stdout.write(message + "\n")
            await self.process.stdout.drain()
        except:
            pass
    
    async def send_image(self, image_data: bytes):
        """Send image using escape sequence"""
        if not image_data:
            return
        
        try:
            b64_image = base64.b64encode(image_data).decode('ascii')
            escape_seq = f"\x1b]IMAGE;{b64_image}\x1b\\"
            self.process.stdout.write(escape_seq)
            await self.process.stdout.drain()
        except Exception as e:
            pass


class MultiplayerGameServer:
    """
    Shared game server for all players
    NOW WITH CHARACTER PORTRAITS!
    """
    def __init__(self, config_path: str = "config"):
        self.config_path = config_path
        
        self.engine = GameEngineRPG(config_path=config_path, player_name="SERVER")
        self.engine.start_game()
        
        self.players: Dict[str, PlayerSession] = {}
        
        self.player_locations: Dict[str, str] = {}
        self.player_inventories: Dict[str, set] = {}
        self.player_health: Dict[str, int] = {}
        self.player_pvp_mode: Dict[str, bool] = {}
        self.player_deaths: Dict[str, int] = {}
        self.player_kills: Dict[str, int] = {}
        
        self.combat_rules = self.load_combat_rules()
        
        # Initialize SD load balancer
        self.sd_balancer = StableDiffusionLoadBalancer()
        
        print("🌐 ZORK RPG Multiplayer Server initialized")
        print(f"📁 World loaded from {config_path}/")
        print(f"⚔️  {len(self.engine.sprite_templates)} sprite types available")
        print(f"🗺️  {len(self.engine.rooms)} rooms in world")
        print(f"📦 {len(self.engine.objects)} objects loaded")
        print(f"⚔️  PvP combat system loaded!")
        print(f"💬 TELL commands enabled (private & broadcast)!")
        print(f"🎨 SD integration: {'ENABLED' if self.sd_balancer.servers else 'DISABLED'}")
        print(f"👤 Character portraits: ENABLED!")
    
    def load_combat_rules(self) -> Dict:
        """Load combat rules from combat.ini"""
        import configparser
        import os
        
        combat_file = f"{self.config_path}/combat.ini"
        if not os.path.exists(combat_file):
            return {
                'player_vs_player': {
                    'base_damage': 10,
                    'weapon_multiplier': 1.0,
                    'can_attack': True,
                    'requires_pvp_mode': True
                }
            }
        
        config = configparser.ConfigParser()
        config.read(combat_file)
        
        rules = {}
        for section in config.sections():
            rules[section] = {}
            for key, value in config[section].items():
                try:
                    if value.lower() in ['true', 'false']:
                        rules[section][key] = value.lower() == 'true'
                    elif '.' in value:
                        rules[section][key] = float(value)
                    else:
                        rules[section][key] = int(value)
                except:
                    rules[section][key] = value
        
        return rules
    
    def add_player(self, player_name: str, session: PlayerSession):
        """Register new player"""
        self.players[player_name] = session
        self.player_locations[player_name] = "entrance_hall"
        self.player_inventories[player_name] = set()
        self.player_health[player_name] = 100
        self.player_pvp_mode[player_name] = False
        self.player_deaths[player_name] = 0
        self.player_kills[player_name] = 0
        
        print(f"✅ Player joined: {player_name} ({len(self.players)} total)")
    
    def remove_player(self, player_name: str):
        """Remove disconnected player"""
        if player_name in self.players:
            location = self.player_locations.get(player_name, "unknown")
            del self.players[player_name]
            if player_name in self.player_locations:
                del self.player_locations[player_name]
            if player_name in self.player_inventories:
                del self.player_inventories[player_name]
            if player_name in self.player_health:
                del self.player_health[player_name]
            if player_name in self.player_pvp_mode:
                del self.player_pvp_mode[player_name]
            if player_name in self.player_deaths:
                del self.player_deaths[player_name]
            if player_name in self.player_kills:
                del self.player_kills[player_name]
            
            print(f"❌ Player left: {player_name} ({len(self.players)} remaining)")
            
            asyncio.create_task(self.broadcast_to_room(
                location, 
                f"💨 {player_name} has disconnected.",
                exclude=player_name
            ))
    
    def get_players_in_room(self, room_id: str) -> list:
        """Get all players in a specific room"""
        return [
            name for name, loc in self.player_locations.items() 
            if loc == room_id
        ]
    
    async def broadcast_to_room(self, room_id: str, message: str, exclude: Optional[str] = None):
        """Send message to all players in a room"""
        players_here = self.get_players_in_room(room_id)
        for player_name in players_here:
            if player_name != exclude and player_name in self.players:
                await self.players[player_name].send(message)
    
    async def broadcast_to_all(self, message: str, exclude: Optional[str] = None):
        """Send message to all connected players"""
        for player_name, session in self.players.items():
            if player_name != exclude:
                await session.send(message)
    
    def format_look_for_player(self, player_name: str, room_id: str) -> str:
        """Generate look output including other players"""
        room = self.engine.rooms.get(room_id)
        if not room:
            return "You are nowhere."
        
        output = [f"\n{room.name}", "=" * len(room.name), room.description]
        
        if room.exits:
            exits = ", ".join(room.exits.keys())
            output.append(f"\nExits: {exits}")
        
        other_players = [p for p in self.get_players_in_room(room_id) if p != player_name]
        if other_players:
            output.append("\n👥 PLAYERS HERE:")
            for other_name in other_players:
                health = self.player_health.get(other_name, 100)
                inventory = self.player_inventories.get(other_name, set())
                pvp_enabled = self.player_pvp_mode.get(other_name, False)
                
                items_held = []
                for item_id in inventory:
                    if item_id in self.engine.objects:
                        items_held.append(self.engine.objects[item_id].name)
                
                holding_text = ""
                if items_held:
                    holding_text = f" (holding: {', '.join(items_held)})"
                
                pvp_indicator = " ⚔️ [PvP]" if pvp_enabled else " 🕊️ [Safe]"
                
                health_bar = f"[{'█' * (health // 10)}{'▒' * ((100 - health) // 10)}]"
                output.append(f"  👤 {other_name} {health_bar} {health}/100 HP{holding_text}{pvp_indicator}")
        
        sprites_here = [s for s in self.engine.sprites.values() 
                       if s.location == room_id and s.is_alive()]
        if sprites_here:
            output.append("\n🚨 ENEMIES:")
            for sprite in sprites_here:
                health_bar = f"[{'█' * (sprite.health // 10)}{'▒' * ((sprite.max_health - sprite.health) // 10)}]"
                items_held = ""
                if sprite.inventory:
                    item_names = [self.engine.objects[id].name for id in sprite.inventory if id in self.engine.objects]
                    if item_names:
                        items_held = f" (holding: {', '.join(item_names)})"
                output.append(f"  ⚔️  {sprite.name} {health_bar} {sprite.health}/{sprite.max_health} HP{items_held}")
        
        objects_here = [obj for obj in self.engine.objects.values() 
                       if obj.location == room_id]
        if objects_here:
            output.append("\nYou can see:")
            for obj in objects_here:
                state_desc = f" ({obj.state})" if obj.state != "normal" else ""
                weapon_mark = " ⚔️ " if obj.is_weapon() else "  "
                output.append(f"{weapon_mark}- {obj.name}{state_desc}")
        
        return "\n".join(output)
    
    # NEW: Generate character portrait prompt!
    def generate_character_prompt(self, player_name: str, inventory: set, health: int) -> str:
        """Generate SD prompt for character portrait showing inventory"""
        
        # Categorize items
        weapons = []
        armor = []
        books = []
        potions = []
        misc = []
        
        for item_id in inventory:
            if item_id not in self.engine.objects:
                continue
            
            obj = self.engine.objects[item_id]
            
            if obj.is_weapon():
                weapons.append(obj.name)
            elif any(x in obj.name.lower() for x in ['armor', 'helmet', 'shield', 'chainmail']):
                armor.append(obj.name)
            elif 'book' in obj.name.lower():
                books.append(obj.name)
            elif any(x in obj.name.lower() for x in ['potion', 'antidote', 'elixir']):
                potions.append(obj.name)
            else:
                misc.append(obj.name)
        
        # Base description
        base = f"Fantasy RPG character portrait of {player_name} the adventurer"
        
        # Build equipment description
        equipment = []
        
        if weapons:
            equipment.append(f"wielding {weapons[0]}")
        
        if armor:
            equipment.append(f"wearing {armor[0]}")
        
        if len(weapons) > 1:
            equipment.append(f"with {weapons[1]} on belt")
        
        if books:
            equipment.append(f"carrying {books[0]}")
        
        if potions:
            if len(potions) == 1:
                equipment.append(f"with {potions[0]} vial")
            else:
                equipment.append(f"with {len(potions)} potion vials on belt")
        
        if misc and len(equipment) < 4:  # Don't overload
            equipment.append(f"holding {misc[0]}")
        
        # Health modifier
        if health < 30:
            condition = ", wounded and bleeding, battle damaged"
        elif health < 60:
            condition = ", slightly injured, worn"
        else:
            condition = ", healthy"
        
        # Assemble prompt
        if equipment:
            equip_text = ", ".join(equipment)
            prompt = f"{base}, {equip_text}{condition}, full body character art, detailed equipment visible, fantasy game illustration, professional quality"
        else:
            prompt = f"{base}, empty handed, simple traveler clothing{condition}, full body character art, fantasy game illustration"
        
        return prompt
    
    async def _generate_and_send_image(self, session: PlayerSession, cache_key: str, prompt: str):
        """Generate and send image in background"""
        if not self.sd_balancer.servers:
            return
        
        try:
            image_data = self.sd_balancer.generate_image(prompt, cache_key=cache_key)
            
            if image_data:
                await session.send_image(image_data)
        except Exception as e:
            print(f"Error generating/sending image: {e}")
    
    async def handle_player_command(self, player_name: str, command: str) -> str:
        """Execute command for a specific player"""
        if not command.strip():
            return ""
        
        location = self.player_locations.get(player_name, "entrance_hall")
        inventory = self.player_inventories.get(player_name, set())
        health = self.player_health.get(player_name, 100)
        
        self.engine.player_location = location
        self.engine.inventory = inventory.copy()
        self.engine.player_health = health
        
        cmd_lower = command.lower().strip()
        
        # NEW: INVENTORY command with character portrait!
        if cmd_lower in ['i', 'inv', 'inventory']:
            # Get text output from engine
            result = self.engine.execute_command(command)
            
            # Generate character portrait!
            session = self.players.get(player_name)
            if session and self.sd_balancer.servers:
                prompt = self.generate_character_prompt(player_name, inventory, health)
                
                # Cache key includes inventory hash (same items = same image!)
                inv_hash = hash(frozenset(inventory))
                cache_key = f"char_{player_name}_{health//20}_{inv_hash}"
                
                print(f"👤 Generating character portrait for {player_name}...")
                asyncio.create_task(self._generate_and_send_image(session, cache_key, prompt))
            
            return result
        
        # TELL command
        if cmd_lower.startswith('tell '):
            parts = command.split(None, 2)
            
            if len(parts) < 3:
                return "Usage: tell <player> <message> OR tell everyone <message>"
            
            target = parts[1].lower()
            message = parts[2].strip()
            
            if target == 'everyone':
                await self.broadcast_to_all(
                    f'📢 {player_name} tells everyone: "{message}"',
                    exclude=player_name
                )
                return f'📢 You tell everyone: "{message}"'
            
            target_player = None
            for pname in self.players.keys():
                if pname.lower() == target:
                    target_player = pname
                    break
            
            if not target_player:
                return f"❌ Player '{parts[1]}' not found. Type 'who' to see connected players."
            
            if target_player == player_name:
                return "❌ You can't tell yourself! (That's just thinking.)"
            
            if target_player in self.players:
                await self.players[target_player].send(
                    f'📧 {player_name} tells you: "{message}"'
                )
            
            return f'📧 You tell {target_player}: "{message}"'
        
        # SAY command
        if cmd_lower.startswith('say '):
            message = command[4:].strip()
            response = f'You say: "{message}"'
            await self.broadcast_to_room(
                location,
                f'💬 {player_name} says: "{message}"',
                exclude=player_name
            )
            return response
        
        # PVP toggle
        if cmd_lower == 'pvp':
            current_mode = self.player_pvp_mode.get(player_name, False)
            self.player_pvp_mode[player_name] = not current_mode
            new_mode = self.player_pvp_mode[player_name]
            
            if new_mode:
                await self.broadcast_to_room(
                    location,
                    f"⚔️  {player_name} has enabled PvP mode!",
                    exclude=player_name
                )
                return "⚔️  PvP mode ENABLED! You can now attack and be attacked by other players!"
            else:
                await self.broadcast_to_room(
                    location,
                    f"🕊️  {player_name} has disabled PvP mode.",
                    exclude=player_name
                )
                return "🕊️  PvP mode DISABLED. You are safe from player attacks."
        
        # WHO command
        if cmd_lower == 'who':
            player_list = [f"  👤 {name} (in {self.player_locations[name]})" 
                          for name in self.players.keys()]
            return f"Connected players ({len(self.players)}):\n" + "\n".join(player_list)
        
        # LOOK command with room image
        if cmd_lower in ['look', 'l']:
            text_output = self.format_look_for_player(player_name, location)
            
            session = self.players.get(player_name)
            if session and self.sd_balancer.servers:
                prompt = self.sd_balancer.sanitize_look_to_prompt(text_output)
                asyncio.create_task(self._generate_and_send_image(session, location, prompt))
            
            return text_output
        
        # Movement
        if cmd_lower in ['n', 's', 'e', 'w', 'north', 'south', 'east', 'west', 'up', 'down', 'u', 'd']:
            old_location = location
            result = self.engine.execute_command(command)
            new_location = self.engine.player_location
            
            if new_location != old_location:
                self.player_locations[player_name] = new_location
                
                await self.broadcast_to_room(
                    old_location,
                    f"💨 {player_name} goes {cmd_lower}.",
                    exclude=player_name
                )
                
                await self.broadcast_to_room(
                    new_location,
                    f"👋 {player_name} arrives.",
                    exclude=player_name
                )
                
                session = self.players.get(player_name)
                if session and self.sd_balancer.servers:
                    look_output = self.format_look_for_player(player_name, new_location)
                    prompt = self.sd_balancer.sanitize_look_to_prompt(look_output)
                    asyncio.create_task(self._generate_and_send_image(session, new_location, prompt))
            
            return self.format_look_for_player(player_name, new_location)
        
        # Execute normal command
        try:
            result = self.engine.execute_command(command)
        except Exception as e:
            return f"⚠️  Command error: {str(e)}"
        
        # Update player state
        self.player_locations[player_name] = self.engine.player_location
        self.player_inventories[player_name] = self.engine.inventory.copy()
        self.player_health[player_name] = self.engine.player_health
        
        # Notify room if item taken/dropped
        if cmd_lower.startswith('take ') or cmd_lower.startswith('get '):
            if "Taken:" in result:
                item_name = result.split("Taken:")[1].strip()
                await self.broadcast_to_room(
                    location,
                    f"👀 {player_name} picks up {item_name}.",
                    exclude=player_name
                )
        elif cmd_lower.startswith('drop '):
            if "Dropped:" in result:
                item_name = result.split("Dropped:")[1].strip()
                await self.broadcast_to_room(
                    location,
                    f"📦 {player_name} drops {item_name}.",
                    exclude=player_name
                )
        
        return result
    
    async def process_global_turn(self):
        """Process game turn effects"""
        messages = self.engine.process_turn()
        
        for msg in messages:
            if "appeared" in msg or "materialized" in msg or "attacks" in msg:
                await self.broadcast_to_all(msg)


# Global server instance
game_server: Optional[MultiplayerGameServer] = None


class ZorkRPGSSHServer(asyncssh.SSHServer):
    """SSH server for multiplayer ZORK RPG"""
    
    def connection_made(self, conn):
        self._conn = conn
    
    def begin_auth(self, username):
        return False
    
    def password_authentication_supported(self):
        return False


async def handle_client(process):
    """Handle one SSH client connection"""
    global game_server
    
    player_name = None
    
    try:
        process.stdout.write("""
╔═══════════════════════════════════════════════════════╗
║    ZORK RPG - WITH CHARACTER PORTRAITS!               ║
║        🎨 Images • 👤 Your Avatar • 🔊 TTS Ready     ║
╚═══════════════════════════════════════════════════════╝

""")
        await process.stdout.drain()
        
        process.stdout.write("Enter your name: ")
        await process.stdout.drain()
        
        player_name = await process.stdin.readline()
        player_name = player_name.strip() or f"Player{len(game_server.players) + 1}"
        
        session = PlayerSession(player_name, process)
        game_server.add_player(player_name, session)
        
        await game_server.broadcast_to_all(
            f"🌟 {player_name} has joined the game!",
            exclude=player_name
        )
        
        process.stdout.write(f"\nWelcome, {player_name}!\n")
        process.stdout.write("Type 'help' for commands, 'i' to see your character!\n\n")
        await process.stdout.drain()
        
        initial_look = game_server.format_look_for_player(player_name, "entrance_hall")
        process.stdout.write(initial_look + "\n")
        await process.stdout.drain()
        
        if game_server.sd_balancer.servers:
            prompt = game_server.sd_balancer.sanitize_look_to_prompt(initial_look)
            asyncio.create_task(game_server._generate_and_send_image(session, "entrance_hall", prompt))
        
        # Main command loop
        while True:
            process.stdout.write(f"\n> ")
            await process.stdout.drain()
            
            try:
                command = await asyncio.wait_for(process.stdin.readline(), timeout=None)
            except:
                break
            
            if not command:
                break
            
            command = command.strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                process.stdout.write("\nGoodbye!\n")
                await process.stdout.drain()
                break
            
            if command.lower() in ['help', '?']:
                help_text = """
COMMANDS:
=========
Movement: north/n, south/s, east/e, west/w
Actions: look/l, inventory/i (shows YOUR character!), examine [obj], take [obj], drop [obj]
Combat: attack [enemy], flee
PvP: pvp (toggle), attack [player]
Social: say [message], tell [player] [message], who
Meta: help, quit

NEW: Type 'i' or 'inventory' to see YOUR CHARACTER with all your items!
"""
                process.stdout.write(help_text)
                await process.stdout.drain()
                continue
            
            if not command:
                continue
            
            try:
                result = await game_server.handle_player_command(player_name, command)
                
                if result:
                    process.stdout.write(result + "\n")
                    await process.stdout.drain()
                
                if game_server.engine.turn_count % 3 == 0:
                    await game_server.process_global_turn()
            
            except Exception as e:
                error_msg = f"⚠️  Error executing command: {str(e)}\n"
                process.stdout.write(error_msg)
                await process.stdout.drain()
                print(f"Command error for {player_name}: {e}")
        
    except Exception as e:
        print(f"Error handling client: {e}")
    
    finally:
        if player_name and player_name in game_server.players:
            game_server.remove_player(player_name)
            await game_server.broadcast_to_all(f"👋 {player_name} has left the game.")


async def start_server(host='0.0.0.0', port=2222, config_path='config'):
    """Start the multiplayer SSH server"""
    global game_server
    
    print("""
╔═══════════════════════════════════════════════════════╗
║   ZORK RPG - SERVER WITH CHARACTER PORTRAITS!         ║
║        Type 'i' to see yourself!                      ║
╚═══════════════════════════════════════════════════════╝
    """)
    
    host_key_file = Path('ssh_host_key')
    if not host_key_file.exists():
        print("⚠️  SSH host key not found. Will generate temporary key.")
    
    game_server = MultiplayerGameServer(config_path=config_path)
    
    print(f"\n🚀 Starting SSH server on {host}:{port}")
    print(f"📁 Config: {config_path}/")
    print("\n⚡ NO PASSWORD REQUIRED!")
    print(f"\nConnect: ssh -p {port} player@{host}")
    print("\nPress Ctrl+C to stop.\n")
    
    try:
        await asyncssh.create_server(
            ZorkRPGSSHServer,
            host,
            port,
            server_host_keys=[host_key_file.as_posix()] if host_key_file.exists() else None,
            process_factory=handle_client,
            encoding='utf-8',
            login_timeout=30
        )
        
        print("✅ Server running! Type 'i' in game to see your character!\n")
        
        await asyncio.Future()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutting down...")
    except Exception as e:
        print(f"\n❌ Server error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZORK RPG Server with Character Portraits')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=2222, help='Port to listen on')
    parser.add_argument('--config', default='config', help='Config directory')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(start_server(args.host, args.port, args.config))
    except KeyboardInterrupt:
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()
