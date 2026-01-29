#!/usr/bin/env python3
"""
SSH Server for ZORK-like adventure game
Allows players to connect via SSH and play the game
"""

import asyncio
import asyncssh
import sys
from game_engine import GameEngine


class GameSSHServer(asyncssh.SSHServer):
    """SSH server that hosts game sessions"""
    
    def connection_made(self, conn):
        print(f'SSH connection received from {conn.get_extra_info("peername")[0]}')

    def connection_lost(self, exc):
        if exc:
            print(f'SSH connection error: {str(exc)}', file=sys.stderr)
        else:
            print('SSH connection closed.')


async def handle_game_session(process):
    """Handle a single game session over SSH"""
    
    # Send welcome banner
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║      ███████╗ ██████╗ ██████╗ ██╗  ██╗                  ║
║      ╚══███╔╝██╔═══██╗██╔══██╗██║ ██╔╝                  ║
║        ███╔╝ ██║   ██║██████╔╝█████╔╝                   ║
║       ███╔╝  ██║   ██║██╔══██╗██╔═██╗                   ║
║      ███████╗╚██████╔╝██║  ██║██║  ██╗                  ║
║      ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                  ║
║                                                           ║
║            A Matrix-Based Text Adventure                 ║
║         Demonstrating Algebraic Game Design              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Welcome, adventurer! Type 'help' for commands, 'quit' to exit.

"""
    process.stdout.write(banner)
    
    # Initialize game engine for this session
    engine = GameEngine(config_path="config")
    
    # Start game
    process.stdout.write(engine.start_game() + "\n\n")
    
    # Game loop
    while True:
        try:
            # Send prompt
            process.stdout.write("> ")
            
            # Read command
            command = await process.stdin.readline()
            if not command:
                break
            
            command = command.strip()
            
            if not command:
                continue
            
            # Handle meta commands
            if command.lower() == 'quit':
                process.stdout.write("\nThanks for playing! Goodbye.\n")
                break
            
            elif command.lower() == 'help':
                help_text = """
AVAILABLE COMMANDS:
  Movement: north, south, east, west, up, down (or n, s, e, w, u, d)
  Actions:  look, examine <object>, take <object>, drop <object>
            inventory (or i), put <object> in <container>
            open <container>, use <object>
  Meta:     save <filename>, load <filename>, help, quit
  
EXAMPLES:
  > look
  > examine sword
  > take water
  > go north
  > put water in freezer
  > wait (pass time)
  > examine water
"""
                process.stdout.write(help_text + "\n")
                continue
            
            elif command.lower().startswith('save '):
                filename = command[5:].strip()
                result = engine.save_game(filename)
                process.stdout.write(result + "\n")
                continue
            
            elif command.lower().startswith('load '):
                filename = command[5:].strip()
                result = engine.load_game(filename)
                process.stdout.write(result + "\n")
                continue
            
            elif command.lower() in ['wait', 'z']:
                process.stdout.write("Time passes...\n")
                turn_messages = engine.process_turn()
                for msg in turn_messages:
                    process.stdout.write(f"\n{msg}\n")
                continue
            
            # Execute game command
            result = engine.execute_command(command)
            process.stdout.write(result + "\n")
            
            # Process turn effects
            turn_messages = engine.process_turn()
            for msg in turn_messages:
                process.stdout.write(f"\n{msg}\n")
            
            process.stdout.write("\n")
            
        except Exception as e:
            process.stdout.write(f"Error: {e}\n")
            continue
    
    process.exit(0)


async def start_ssh_server(host='0.0.0.0', port=2222):
    """Start the SSH game server"""
    
    print(f"Starting ZORK SSH server on {host}:{port}")
    print("Players can connect with: ssh -p 2222 player@localhost")
    print("(No password required for demo - press Ctrl+C to stop)\n")
    
    # Create a simple host key if it doesn't exist
    await asyncssh.create_server(
        GameSSHServer,
        host,
        port,
        server_host_keys=['ssh_host_key'],
        process_factory=handle_game_session,
        encoding='utf-8'
    )
    
    # Keep running
    await asyncio.Future()  # Run forever


def main():
    try:
        asyncio.run(start_ssh_server())
    except KeyboardInterrupt:
        print("\nShutting down SSH server...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
