#!/usr/bin/env python3
"""
ZORK RPG - Multiplayer SSH Server
Player 1 hosts, others connect via SSH
Shared world state, real-time multiplayer!
"""

import asyncio
import asyncssh
import sys
from pathlib import Path
from game_engine_rpg import GameEngineRPG
from typing import Dict, Optional
import json


class PlayerSession:
    """Represents one connected player"""
    def __init__(self, player_name: str, process):
        self.player_name = player_name
        self.process = process
        self.location = "entrance_hall"
        self.health = 100
        self.inventory = set()
        self.last_message = ""
    
    async def send(self, message: str):
        """Send message to this player"""
        try:
            self.process.stdout.write(message + "\n")
            await self.process.stdout.drain()
        except:
            pass  # Player disconnected


class MultiplayerGameServer:
    """
    Shared game server for all players
    ONE world, many players
    """
    def __init__(self, config_path: str = "config"):
        self.config_path = config_path
        
        # Shared world engine (one for all players!)
        self.engine = GameEngineRPG(config_path=config_path, player_name="SERVER")
        self.engine.start_game()
        
        # Track all connected players
        self.players: Dict[str, PlayerSession] = {}
        
        # Track player states
        self.player_locations: Dict[str, str] = {}
        self.player_inventories: Dict[str, set] = {}
        self.player_health: Dict[str, int] = {}
        
        print("🌐 ZORK RPG Multiplayer Server initialized")
        print(f"📁 World loaded from {config_path}/")
        print(f"⚔️  {len(self.engine.sprite_templates)} sprite types available")
        print(f"🗺️  {len(self.engine.rooms)} rooms in world")
        print(f"📦 {len(self.engine.objects)} objects loaded")
    
    def add_player(self, player_name: str, session: PlayerSession):
        """Register new player"""
        self.players[player_name] = session
        self.player_locations[player_name] = "entrance_hall"
        self.player_inventories[player_name] = set()
        self.player_health[player_name] = 100
        
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
            
            print(f"❌ Player left: {player_name} ({len(self.players)} remaining)")
            
            # Notify others in that location
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
        
        # List exits
        if room.exits:
            exits = ", ".join(room.exits.keys())
            output.append(f"\nExits: {exits}")
        
        # List other players in room
        other_players = [p for p in self.get_players_in_room(room_id) if p != player_name]
        if other_players:
            output.append("\n👥 PLAYERS HERE:")
            for other_name in other_players:
                health = self.player_health.get(other_name, 100)
                inventory = self.player_inventories.get(other_name, set())
                
                # Show what they're holding
                items_held = []
                for item_id in inventory:
                    if item_id in self.engine.objects:
                        items_held.append(self.engine.objects[item_id].name)
                
                holding_text = ""
                if items_held:
                    holding_text = f" (holding: {', '.join(items_held)})"
                
                health_bar = f"[{'█' * (health // 10)}{'░' * ((100 - health) // 10)}]"
                output.append(f"  👤 {other_name} {health_bar} {health}/100 HP{holding_text}")
        
        # List sprites in room
        sprites_here = [s for s in self.engine.sprites.values() 
                       if s.location == room_id and s.is_alive()]
        if sprites_here:
            output.append("\n🚨 ENEMIES:")
            for sprite in sprites_here:
                health_bar = f"[{'█' * (sprite.health // 10)}{'░' * ((sprite.max_health - sprite.health) // 10)}]"
                items_held = ""
                if sprite.inventory:
                    item_names = [self.engine.objects[id].name for id in sprite.inventory if id in self.engine.objects]
                    if item_names:
                        items_held = f" (holding: {', '.join(item_names)})"
                output.append(f"  ⚔️  {sprite.name} {health_bar} {sprite.health}/{sprite.max_health} HP{items_held}")
        
        # List objects in room
        objects_here = [obj for obj in self.engine.objects.values() 
                       if obj.location == room_id]
        if objects_here:
            output.append("\nYou can see:")
            for obj in objects_here:
                state_desc = f" ({obj.state})" if obj.state != "normal" else ""
                weapon_mark = " ⚔️ " if obj.is_weapon() else "  "
                output.append(f"{weapon_mark}- {obj.name}{state_desc}")
        
        return "\n".join(output)
    
    async def handle_player_command(self, player_name: str, command: str) -> str:
        """Execute command for a specific player"""
        if not command.strip():
            return ""
        
        # Get player's current state
        location = self.player_locations.get(player_name, "entrance_hall")
        inventory = self.player_inventories.get(player_name, set())
        health = self.player_health.get(player_name, 100)
        
        # Set engine state to this player's state
        self.engine.player_location = location
        self.engine.inventory = inventory.copy()
        self.engine.player_health = health
        
        # Handle special multiplayer commands
        cmd_lower = command.lower().strip()
        
        if cmd_lower.startswith('say '):
            message = command[4:].strip()
            response = f'You say: "{message}"'
            # Broadcast to others in room
            await self.broadcast_to_room(
                location,
                f'💬 {player_name} says: "{message}"',
                exclude=player_name
            )
            return response
        
        if cmd_lower == 'who':
            player_list = [f"  👤 {name} (in {self.player_locations[name]})" 
                          for name in self.players.keys()]
            return f"Connected players ({len(self.players)}):\n" + "\n".join(player_list)
        
        if cmd_lower in ['look', 'l']:
            return self.format_look_for_player(player_name, location)
        
        # Handle movement - notify others
        if cmd_lower in ['n', 's', 'e', 'w', 'north', 'south', 'east', 'west', 'up', 'down', 'u', 'd']:
            old_location = location
            result = self.engine.execute_command(command)
            new_location = self.engine.player_location
            
            if new_location != old_location:
                # Player moved!
                self.player_locations[player_name] = new_location
                
                # Notify old room
                await self.broadcast_to_room(
                    old_location,
                    f"💨 {player_name} goes {cmd_lower}.",
                    exclude=player_name
                )
                
                # Notify new room
                await self.broadcast_to_room(
                    new_location,
                    f"👋 {player_name} arrives.",
                    exclude=player_name
                )
            
            # Show the new room with players
            return self.format_look_for_player(player_name, new_location)
        
        # Execute normal command
        result = self.engine.execute_command(command)
        
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
        """Process game turn effects (spawns, transformations, sprite AI)"""
        messages = self.engine.process_turn()
        
        # Broadcast important events to everyone
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
        # Allow any username (no password needed for demo)
        return True
    
    def password_authentication_supported(self):
        return True
    
    def validate_password(self, username, password):
        # Accept any password for demo
        return True


async def handle_client(process):
    """Handle one SSH client connection"""
    global game_server
    
    try:
        # Welcome message
        process.stdout.write("""
╔════════════════════════════════════════════════╗
║    ZORK RPG - MULTIPLAYER SSH SERVER          ║
║         Combat • Sprites • Survival           ║
╚════════════════════════════════════════════════╝

""")
        await process.stdout.drain()
        
        # Get player name
        process.stdout.write("Enter your name: ")
        await process.stdout.drain()
        
        player_name = await process.stdin.readline()
        player_name = player_name.strip() or f"Player{len(game_server.players) + 1}"
        
        # Create session
        session = PlayerSession(player_name, process)
        game_server.add_player(player_name, session)
        
        # Announce join
        await game_server.broadcast_to_all(
            f"🌟 {player_name} has joined the game!",
            exclude=player_name
        )
        
        # Show welcome
        process.stdout.write(f"\nWelcome, {player_name}!\n")
        process.stdout.write("Type 'help' for commands, 'who' to see players, 'quit' to exit.\n\n")
        await process.stdout.drain()
        
        # Show initial room
        initial_look = game_server.format_look_for_player(player_name, "entrance_hall")
        process.stdout.write(initial_look + "\n")
        await process.stdout.drain()
        
        # Main command loop
        while True:
            # Prompt
            process.stdout.write(f"\n> ")
            await process.stdout.drain()
            
            # Get command
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
Actions: look/l, examine [obj], take [obj], drop [obj], inventory/i
Combat: attack [enemy], attack [enemy] with [weapon], flee
Social: say [message], who (list players)
Items: drink [potion], use [object]
Meta: help, quit

MULTIPLAYER:
============
- See other players in your room
- They see what you pick up/drop
- Use 'say' to communicate
- Real-time shared world!
"""
                process.stdout.write(help_text)
                await process.stdout.drain()
                continue
            
            if not command:
                continue
            
            # Execute command
            result = await game_server.handle_player_command(player_name, command)
            
            if result:
                process.stdout.write(result + "\n")
                await process.stdout.drain()
            
            # Process global turn effects occasionally
            if game_server.engine.turn_count % 3 == 0:
                await game_server.process_global_turn()
        
    except Exception as e:
        print(f"Error handling client {player_name}: {e}")
    
    finally:
        # Clean up
        if player_name:
            game_server.remove_player(player_name)
            await game_server.broadcast_to_all(f"👋 {player_name} has left the game.")


async def start_server(host='0.0.0.0', port=2222, config_path='config'):
    """Start the multiplayer SSH server"""
    global game_server
    
    print("""
╔════════════════════════════════════════════════╗
║     ZORK RPG - MULTIPLAYER SERVER (SSH)       ║
╚════════════════════════════════════════════════╝
    """)
    
    # Check for host key
    host_key_file = Path('ssh_host_key')
    if not host_key_file.exists():
        print("⚠️  SSH host key not found. Generating...")
        print("Run: ssh-keygen -t rsa -f ssh_host_key -N \"\"")
        print("\nOr the server will generate a temporary key.")
    
    # Initialize game server
    game_server = MultiplayerGameServer(config_path=config_path)
    
    print(f"\n🚀 Starting SSH server on {host}:{port}")
    print(f"📁 Config loaded from: {config_path}/")
    print("\nPlayers can connect with:")
    print(f"   ssh -p {port} player@{host}")
    print("\nPress Ctrl+C to stop the server.\n")
    
    try:
        await asyncssh.create_server(
            ZorkRPGSSHServer,
            host,
            port,
            server_host_keys=[host_key_file.as_posix()] if host_key_file.exists() else None,
            process_factory=handle_client,
            encoding='utf-8'
        )
        
        print("✅ Server is running! Waiting for players...\n")
        
        # Run forever
        await asyncio.Future()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutting down...")
    except Exception as e:
        print(f"\n❌ Server error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZORK RPG Multiplayer SSH Server')
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
