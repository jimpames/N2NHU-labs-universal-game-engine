#!/usr/bin/env python3
"""
Simple terminal-based runner for the ZORK-like adventure game
"""

from game_engine import GameEngine
import sys


def print_banner():
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
    print(banner)


def print_help():
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
    print(help_text)


def main():
    print_banner()
    
    # Initialize game engine
    engine = GameEngine(config_path="config")
    
    # Start game
    print(engine.start_game())
    print()
    
    # Main game loop
    while True:
        try:
            command = input("> ").strip()
            
            if not command:
                continue
            
            # Handle meta commands
            if command.lower() == 'quit':
                print("\nThanks for playing! Goodbye.")
                break
            
            elif command.lower() == 'help':
                print_help()
                continue
            
            elif command.lower().startswith('save '):
                filename = command[5:].strip()
                print(engine.save_game(filename))
                continue
            
            elif command.lower().startswith('load '):
                filename = command[5:].strip()
                print(engine.load_game(filename))
                continue
            
            elif command.lower() in ['wait', 'z']:
                print("Time passes...")
                turn_messages = engine.process_turn()
                for msg in turn_messages:
                    print(f"\n{msg}")
                continue
            
            # Execute game command
            result = engine.execute_command(command)
            print(result)
            
            # Process turn effects
            turn_messages = engine.process_turn()
            for msg in turn_messages:
                print(f"\n{msg}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nGame interrupted. Type 'quit' to exit properly.")
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
