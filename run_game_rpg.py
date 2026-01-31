#!/usr/bin/env python3
"""
ZORK RPG - Enhanced with combat, health, sprites, and VOICE!
"""

import sys
from game_engine_rpg import GameEngineRPG
from voice_synth import VoiceSynthesizer


def main():
    print("""
╔════════════════════════════════════════════════╗
║         ZORK RPG - MATRIX ADVENTURE           ║
║    Combat • Health • Sprites • Survival       ║
║              🔊 VOICE ENABLED!                ║
╚════════════════════════════════════════════════╝
    """)
    
    # Initialize voice
    voice = VoiceSynthesizer(enabled=True)
    voice_enabled = True
    
    print("🔊 Voice synthesis is ENABLED!")
    print("Type 'voice' to toggle voice on/off\n")
    
    voice.speak("Welcome to ZORK RPG!")
    
    player_name = input("Enter your name (default: Hero): ").strip() or "Hero"
    
    # Initialize engine
    engine = GameEngineRPG(config_path="config", player_name=player_name)
    
    print(f"\nWelcome, {player_name}!")
    print("\n⚠️  WARNING: Your health depletes over time. Find potions to survive!")
    print("Type 'help' for commands, 'health' to check status, 'quit' to exit.\n")
    
    # Start game
    initial_text = engine.start_game()
    print(initial_text)
    if voice_enabled:
        voice.speak(initial_text)
    
    health_status = engine.check_health()
    print(f"\n{health_status}")
    if voice_enabled:
        voice.speak(health_status)
    
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
            if voice_enabled:
                voice.speak("Thanks for playing!")
            break
        
        if command.lower() == 'voice':
            voice_enabled = not voice_enabled
            voice.enabled = voice_enabled
            if voice_enabled:
                msg = "🔊 Voice synthesis ENABLED!"
                print(msg)
                voice.speak(msg)
            else:
                msg = "🔇 Voice synthesis DISABLED."
                print(msg)
            continue
        
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
System: save [name], load [name], voice (toggle voice), quit

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
        
        # Speak result if voice enabled
        if voice_enabled and result.strip():
            voice_type = get_voice_type(result)
            voice.speak(result, voice_type)
        
        # Process turn
        messages = engine.process_turn()
        for msg in messages:
            print(msg)
            if voice_enabled and msg.strip():
                voice_type = get_voice_type(msg)
                voice.speak(msg, voice_type)
        
        # Show health periodically
        if engine.turn_count % 5 == 0 and engine.player_health > 0:
            health_msg = engine.check_health()
            print(f"\n{health_msg}")
            if voice_enabled:
                voice.speak(health_msg)


def get_voice_type(text):
    """Determine voice type from text"""
    text_lower = text.lower()
    
    if 'troll' in text_lower and any(word in text_lower for word in ['says', 'roars', 'attacks']):
        return 'troll'
    elif 'goblin' in text_lower and any(word in text_lower for word in ['says', 'attacks']):
        return 'goblin'
    elif 'dragon' in text_lower and any(word in text_lower for word in ['says', 'roars', 'attacks']):
        return 'dragon'
    elif 'merchant' in text_lower and 'says' in text_lower:
        return 'merchant'
    else:
        return 'narrator'


if __name__ == "__main__":
    main()
