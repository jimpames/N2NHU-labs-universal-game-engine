# ZORK-like Text Adventure Game
## Matrix-Based Algebraic Design Demo

GPL3

by N2NHU Labs for Applied AI

blame: j p ames

VERSION 2

30 Jan 2026 new features:

- SSH multi player
- health points
- auto spawning demonds, bosses and trolls
- random materializing health potions
- physics for ice and water

  HOWTO play:

  make a config folder in your folder for the game and put all .ini in the config folder

  Start SSH server:            python ssh_server_multiplayer_rpg.py

  players can connect with:   ssh -p 2222 player@ip.of.ssh.server




This is a demonstration of how **algebraic design with matrices** can create complex gameplay with minimal code.

## 🎯 Key Architecture Concepts

### The Matrix Approach

Instead of hardcoding every interaction, we use **three matrices** that work together:

1. **Object Matrix** - Every object has properties (defined in `objects.ini`)
2. **Verb Matrix** - Every action/verb is defined (in `verbs.ini`)  
3. **Action Matrix** - Maps which verbs work with which objects

This means:
- ✅ "take knife" works (knife has `take` in valid_verbs)
- ❌ "eat knife" fails (knife doesn't have `eat` in valid_verbs)
- ❌ "take room" fails (room has takeable=false)

**The beautiful part:** Adding a new item is just adding data, not code!

### Configuration-Driven Design

Everything is in `.ini` files:
- `verbs.ini` - All available actions
- `objects.ini` - All items and their properties
- `rooms.ini` - All locations and exits
- `transformations.ini` - State change rules

### Dynamic Object Transformations

The `transformations.ini` file defines rules like:
```ini
[water_to_ice]
object_id = water
state = liquid
location_has_property = cold
turns_required = 3
new_object_id = ice
```

This means: "If water (in liquid state) is in a room with the 'cold' property for 3 turns, transform it to ice"

**No hardcoding needed!** The game engine checks these rules every turn.

## 🎮 Game Features

### Implemented Features
- ✅ Matrix-based verb/object system
- ✅ Multi-room exploration with exits
- ✅ Inventory management
- ✅ Container objects (put things in other things)
- ✅ State transformations (water → ice)
- ✅ Turn-based time system
- ✅ Save/Load game states
- ✅ SSH interface for remote play
- ✅ Terminal interface for local play

### The Water → Ice Demo

Try this in the game to see emergent behavior:

```
> take water
> go west          (to kitchen)
> go north         (to freezer - a COLD room)
> drop water
> wait
> wait
> wait
> examine water    (it's now ice!)
```

The freezer has `cold = true` in its properties. The transformation rule automatically triggers!

## 🏗️ File Structure

```
zork_game/
├── game_engine.py          # Core engine with matrix logic
├── run_game.py             # Terminal interface
├── ssh_server.py           # SSH server for remote play
├── config/
│   ├── verbs.ini          # Verb definitions
│   ├── objects.ini        # Object definitions  
│   ├── rooms.ini          # Room layout
│   └── transformations.ini # State change rules
└── README.md              # This file
```

## 🚀 How to Run

### Local Terminal Play

```bash
# Install dependencies
pip install asyncssh --break-system-packages

# Run the game
python3 run_game.py
```

### SSH Server Mode

```bash
# Generate SSH host key (first time only)
ssh-keygen -t rsa -f ssh_host_key -N ""

# Start SSH server
python3 ssh_server.py

# Connect from another terminal
ssh -p 2222 player@localhost
```

## 🎓 Teaching Points

This demo illustrates:

1. **Separation of Concerns**
   - Data (`.ini` files) vs Logic (`game_engine.py`)
   - Easy to add content without touching code

2. **Algebraic Design**
   - Objects × Verbs = Action Matrix
   - Simple matrix lookups replace complex conditionals

3. **Data-Driven Architecture**
   - Game behavior defined by configuration
   - Transformations as declarative rules

4. **Emergent Complexity**
   - Simple rules create complex interactions
   - Water+Freezer+Time = Ice (automatically!)

5. **Practical Engineering**
   - SSH avoids web framework complexity
   - JSON for save states
   - Clean separation enables testing

## 🔧 Extending the Game

### Add a New Object

Edit `config/objects.ini`:
```ini
[torch]
name = burning torch
description = A wooden torch with flickering flames
location = entrance_hall
takeable = true
valid_verbs = take, drop, examine, use
```

### Add a New Transformation

Edit `config/transformations.ini`:
```ini
[ice_to_water]
object_id = ice
state = frozen
turns_required = 5
new_object_id = water
message = The ice has melted back into water!
```

### Add a New Room

Edit `config/rooms.ini`:
```ini
[dungeon]
name = Dark Dungeon
description = A damp, dark cell with chains on the walls
north = entrance_hall
```

## 🎯 Commands Reference

**Movement:** `north`, `south`, `east`, `west`, `up`, `down` (or `n`, `s`, `e`, `w`, `u`, `d`)

**Actions:** 
- `look` - Examine current room
- `examine <object>` - Look closely at something
- `take <object>` - Pick up an item
- `drop <object>` - Drop an item
- `inventory` (or `i`) - Show what you're carrying
- `put <object> in <container>` - Store items
- `open <container>` - See what's inside
- `wait` (or `z`) - Pass time (advance turn counter)

**Meta:**
- `save <filename>` - Save game
- `load <filename>` - Load game
- `help` - Show help
- `quit` - Exit

## 💡 Code Highlights

### The Action Matrix Check
```python
def can_perform_action(self, verb_id: str, obj: GameObject) -> bool:
    """Check action matrix if verb can be performed on object"""
    return verb_id in self.action_matrix.get(obj.id, set())
```

Just one line! The matrix does all the work.

### Transformation Processing
```python
def check_transformation(self, transformation: Dict[str, Any]) -> Optional[str]:
    # Check all conditions (object, state, location, turns)
    # If all match, apply transformation
    # Return message if transformation occurred
```

This is the "emergent behavior" engine - rules create complexity!

## 📚 For Your Team Demo

**Show them:**
1. How little code is needed (game_engine.py is ~400 lines)
2. How adding content doesn't require code changes
3. The water→ice transformation happening automatically
4. How the action matrix prevents nonsensical commands
5. The SSH server simplicity vs web frameworks

**Key takeaway:** Good architecture multiplies developer productivity!

---

Built to demonstrate the power of algebraic game design 🎮
