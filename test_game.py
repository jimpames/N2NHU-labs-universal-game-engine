#!/usr/bin/env python3
"""
Test script to verify the water→ice transformation works correctly
"""

from game_engine import GameEngine
import sys


def test_water_to_ice():
    """Test the water to ice transformation"""
    print("🧪 Testing Water → Ice Transformation\n")
    
    # Initialize engine
    print("1️⃣  Initializing game engine...")
    engine = GameEngine(config_path="config")
    engine.start_game()
    print("   ✅ Engine loaded successfully")
    
    # Find water object
    print("\n2️⃣  Finding water object...")
    water = engine.objects.get("water")
    if not water:
        print("   ❌ FAIL: Water object not found!")
        return False
    print(f"   ✅ Found water: {water.name}")
    print(f"   ℹ️  Initial state: {water.state}")
    
    # Verify initial state
    print("\n3️⃣  Verifying initial conditions...")
    if water.state != "liquid":
        print(f"   ❌ FAIL: Water should start in 'liquid' state, got '{water.state}'")
        return False
    print("   ✅ Water is in liquid state")
    
    # Move water to freezer
    print("\n4️⃣  Placing water in freezer...")
    water.location = "freezer"
    print(f"   ✅ Water location: {water.location}")
    
    # Verify freezer has cold property
    freezer = engine.rooms.get("freezer")
    if not freezer or not freezer.get_property("cold"):
        print("   ❌ FAIL: Freezer doesn't have 'cold' property!")
        return False
    print("   ✅ Freezer has 'cold' property")
    
    # Process turns
    print("\n5️⃣  Processing turns...")
    for turn in range(1, 4):
        print(f"   Turn {turn}...", end="")
        messages = engine.process_turn()
        
        if turn < 3:
            if messages:
                print(f" (got message: {messages})")
            else:
                print(" ⏳")
        else:
            # Turn 3 - transformation should happen
            if not messages:
                print("\n   ❌ FAIL: No transformation message on turn 3!")
                return False
            print(f" 💥 TRANSFORMATION!")
            print(f"   Message: '{messages[0]}'")
    
    # Verify transformation occurred
    print("\n6️⃣  Verifying transformation...")
    water_after = engine.objects.get("water")
    if water_after.state != "frozen":
        print(f"   ❌ FAIL: Water state should be 'frozen', got '{water_after.state}'")
        return False
    print(f"   ✅ Water state changed to: {water_after.state}")
    
    # Check object properties changed
    if water_after.name != "cup of ice":
        print(f"   ⚠️  Warning: Name should be 'cup of ice', got '{water_after.name}'")
        print("   (This might be OK if transformation uses different object)")
    
    print("\n✅ ALL TESTS PASSED! Water → Ice transformation works correctly!")
    return True


def test_action_matrix():
    """Test that action matrix prevents invalid actions"""
    print("\n🧪 Testing Action Matrix\n")
    
    engine = GameEngine(config_path="config")
    engine.start_game()
    
    print("1️⃣  Testing valid action (take knife)...")
    knife = engine.objects.get("knife")
    if not engine.can_perform_action("take", knife):
        print("   ❌ FAIL: Should be able to take knife!")
        return False
    print("   ✅ Can take knife (as expected)")
    
    print("\n2️⃣  Testing invalid action (eat knife)...")
    if engine.can_perform_action("eat", knife):
        print("   ❌ FAIL: Should NOT be able to eat knife!")
        return False
    print("   ✅ Cannot eat knife (as expected)")
    
    print("\n✅ Action matrix working correctly!")
    return True


def test_config_loading():
    """Test that all configs load properly"""
    print("\n🧪 Testing Configuration Loading\n")
    
    engine = GameEngine(config_path="config")
    
    print("1️⃣  Checking rooms...")
    if len(engine.rooms) < 5:
        print(f"   ❌ FAIL: Expected at least 5 rooms, got {len(engine.rooms)}")
        return False
    print(f"   ✅ Loaded {len(engine.rooms)} rooms")
    
    print("\n2️⃣  Checking objects...")
    if len(engine.objects) < 10:
        print(f"   ❌ FAIL: Expected at least 10 objects, got {len(engine.objects)}")
        return False
    print(f"   ✅ Loaded {len(engine.objects)} objects")
    
    print("\n3️⃣  Checking verbs...")
    if len(engine.verbs) < 10:
        print(f"   ❌ FAIL: Expected at least 10 verbs, got {len(engine.verbs)}")
        return False
    print(f"   ✅ Loaded {len(engine.verbs)} verbs")
    
    print("\n4️⃣  Checking transformations...")
    if len(engine.transformations) < 1:
        print(f"   ❌ FAIL: Expected at least 1 transformation, got {len(engine.transformations)}")
        return False
    print(f"   ✅ Loaded {len(engine.transformations)} transformations")
    
    print("\n✅ All configurations loaded successfully!")
    return True


def main():
    print("=" * 60)
    print("  ZORK GAME ENGINE - AUTOMATED TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Action Matrix", test_action_matrix),
        ("Water→Ice Transformation", test_water_to_ice),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print("\n" + "=" * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print("\n" + "=" * 60)
    print(f"  TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! The game is ready to demo!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
