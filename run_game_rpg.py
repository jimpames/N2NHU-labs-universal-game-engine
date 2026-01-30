#!/usr/bin/env python3
"""
ZORK RPG - Enhanced with combat, health, and sprites!
"""

import sys
from game_engine_rpg import GameEngineRPG


def main():
    print("""
╔════════════════════════════════════════════════╗
║         ZORK RPG - MATRIX ADVENTURE           ║
║    Combat • Health • Sprites • Survival       ║
╚════════════════════════════════════════════════╝
    """)
    
    player_name = input("Enter your name (default: Hero): ").strip() or "Hero"
    
    # Initialize engine
    engine = GameEngineRPG(config_path="config", player_name=player_name)
    
    print(f"\nWelcome, {player_name}!")
    print("\n⚠️  WARNING: Your health depletes over time. Find potions to survive!")
    print("Type 'help' for commands, 'health' to check status, 'quit' to exit.\n")
    
    # Start game
    print(engine.start_game())
    print(f"\n{engine.check_health()}")
    
    # Main game loop
    while True:
        # Check if dead
        if engine.player_health <= 0:
            print("\n" + "="*50)
            print("💀 GAME OVER")
            print("="*50)
            print(f"Turns survived: {engine.turn_count}")
            print(f"Enemies slain: {engine.kills}")
            print(f"Deaths: {engine.deaths}")
            print(f"Potions consumed: {engine.potions_consumed}")
            
            choice = input("\nPlay again? (y/n): ").lower()
            if choice == 'y':
                engine = GameEngineRPG(config_path="config", player_name=player_name)
                print(engine.start_game())
                print(f"\n{engine.check_health()}")
                continue
            else:
                break
        
        # Get command
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing!")
            break
        
        if not command:
            continue
        
        # Handle meta commands
        if command.lower() in ['quit', 'exit', 'q']:
            print("\nThanks for playing!")
            break
        
        if command.lower() in ['help', '?']:
            print("""
COMMANDS:
=========
Movement: north/n, south/s, east/e, west/w, up, down
Actions: look/l, examine [object], take [object], drop [object]
         inventory/i, health/status
Combat: attack [enemy], attack [enemy] with [weapon], flee/run
Items: drink [potion], use [object]
Containers: open [container], close [container], put [object] in [container]
System: save [name], load [name], quit

SURVIVAL TIPS:
==============
- Your health depletes every 5 turns - find potions!
- Weapons do more damage - pick them up!
- Sprites can pick up items - be quick!
- Hostile sprites attack on sight!
- Flee if you're low on health!
            """)
            continue
        
        # Handle save/load
        if command.lower().startswith('save '):
            filename = command[5:].strip()
            print(engine.save_game(filename))
            continue
        
        if command.lower().startswith('load '):
            filename = command[5:].strip()
            print(engine.load_game(filename))
            continue
        
        if command.lower() == 'wait' or command.lower() == 'z':
            print("Time passes...")
            messages = engine.process_turn()
            for msg in messages:
                print(msg)
            if engine.player_health > 0 and engine.turn_count % 5 == 0:
                print(f"\n{engine.check_health()}")
            continue
        
        # Execute command
        result = engine.execute_command(command)
        print(result)
        
        # Process turn
        messages = engine.process_turn()
        for msg in messages:
            print(msg)
        
        # Show health periodically
        if engine.turn_count % 5 == 0 and engine.player_health > 0:
            print(f"\n{engine.check_health()}")


if __name__ == "__main__":
    main()
