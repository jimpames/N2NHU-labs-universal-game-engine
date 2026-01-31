#!/usr/bin/env python3
"""
Quick Voice Test Script
Test the voice synthesis with game-like scenarios
"""

from voice_synth import VoiceSynthesizer
import time

def test_voices():
    """Test different voice types"""
    
    synth = VoiceSynthesizer(enabled=True)
    
    print("=" * 60)
    print("VOICE SYNTHESIS TEST")
    print("=" * 60)
    print()
    
    # Test 1: Narrator (Room Description)
    print("Test 1: NARRATOR - Room Description")
    text = "You stand in a grand entrance hall. Dusty tapestries hang on stone walls, and a chandelier dangles precariously overhead."
    print(f"Speaking: {text}")
    synth.speak(text, 'narrator')
    time.sleep(5)
    print()
    
    # Test 2: Combat (Narrator)
    print("Test 2: NARRATOR - Combat")
    text = "You attack the brutal troll with rusty sword for 25 damage!"
    print(f"Speaking: {text}")
    synth.speak(text, 'narrator')
    time.sleep(3)
    print()
    
    # Test 3: Troll Voice (Deep, Slow)
    print("Test 3: TROLL - NPC Dialogue")
    text = "Me smash! Give gold or me crush bones!"
    print(f"Speaking: {text}")
    synth.speak(text, 'troll')
    time.sleep(4)
    print()
    
    # Test 4: Goblin Voice (Fast, High)
    print("Test 4: GOBLIN - NPC Dialogue")
    text = "Hehe! Shiny things! Mine mine mine! So many pretties!"
    print(f"Speaking: {text}")
    synth.speak(text, 'goblin')
    time.sleep(3)
    print()
    
    # Test 5: Dragon Voice (Very Slow, Booming)
    print("Test 5: DRAGON - Boss Dialogue")
    text = "You dare disturb my slumber, mortal? Your bones shall decorate my hoard!"
    print(f"Speaking: {text}")
    synth.speak(text, 'dragon')
    time.sleep(6)
    print()
    
    # Test 6: Player Message
    print("Test 6: NARRATOR - Player Action")
    text = "You pick up the rusty sword. It feels heavy in your hands."
    print(f"Speaking: {text}")
    synth.speak(text, 'player')
    time.sleep(4)
    print()
    
    # Test 7: Merchant Voice
    print("Test 7: MERCHANT - NPC Dialogue")
    text = "Welcome, traveler! I have many fine wares for sale today!"
    print(f"Speaking: {text}")
    synth.speak(text, 'merchant')
    time.sleep(4)
    print()
    
    print("=" * 60)
    print("VOICE TEST COMPLETE!")
    print("=" * 60)
    print()
    print("Did you hear all the voices?")
    print()
    print("Voice characteristics:")
    print("  - Narrator: Normal speed, clear")
    print("  - Troll: Slow, deep, menacing")
    print("  - Goblin: Fast, high-pitched, frantic")
    print("  - Dragon: Very slow, booming, epic")
    print("  - Merchant: Friendly, welcoming")
    print()
    print("Ready to add to the game? Run:")
    print("  python ssh_server_multiplayer_rpg.py")
    print()


def interactive_test():
    """Interactive voice test"""
    
    synth = VoiceSynthesizer(enabled=True)
    
    print("\n" + "=" * 60)
    print("INTERACTIVE VOICE TEST")
    print("=" * 60)
    print()
    print("Type text and choose a voice type to hear it spoken.")
    print("Voice types: narrator, troll, goblin, dragon, merchant")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        text = input("\nEnter text to speak (or 'quit'): ").strip()
        
        if text.lower() == 'quit':
            break
        
        if not text:
            continue
        
        voice_type = input("Voice type (narrator/troll/goblin/dragon/merchant): ").strip().lower()
        
        if voice_type not in ['narrator', 'troll', 'goblin', 'dragon', 'merchant']:
            voice_type = 'narrator'
            print(f"Unknown voice type, using 'narrator'")
        
        print(f"\nSpeaking as {voice_type}...")
        synth.speak(text, voice_type)
    
    print("\nGoodbye!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_test()
    else:
        test_voices()
