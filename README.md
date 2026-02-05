# ZORK-like Text Adventure Game
## Matrix-Based Algebraic Design Demo

This is a demonstration of how **algebraic design with matrices** can create complex gameplay with minimal code.

version 7
- v7 has character avatars when you inventory so you can see what they are carrying

- start the  avatar version with the avatar server: speech_ssh_server_with_portraits.py

- use the graphics client below

version 6 is new as of 4 feb 
- delivers graphics client and stable diffusion as render engine

- ======================================================================

to play graphics version:  demo: https://youtu.be/H9VQkj39AJU?si=pLQKebWuOQnrheS2
=====================================================================
put stablediffusion.ini in the config dir

mark your SD IP true in the INI and all the others FLASE
=====================================================================
bring up automatic1111 in API and LISTEN mode
=====================================================================
build your venv for the server
cd zorkserver
venv\scripts\activate
pip install -r image-server-requirements.txt

load the graphics  server : python speech_ssh_server_enhanced_SD.py
=======================================================================================
build your venv for the client
cd zorkclient
venv\scripts\activate
pip install -r image-client-requirements.txt

load the graphics client : python voice_image_ssh_client.py
=============================================================================

BOOK:  390 page theory of operation and design book now live in github - PDF - enjoy - GPL3 book  31 jan 2026

Kindle Edition theory of operation:   https://www.amazon.com/dp/B0GKX969Y2

GPL3 code

a product of the n2nhu lab for applied ai

video demo: https://youtu.be/ImDskO5664g?si=w7o0u9tJvVKwifTi

scaling / security enhancement coming soon in v6 by summer: https://github.com/jimpames/N2NHU-labs-universal-game-engine/blob/main/Planned%20Enhancements_%20Algebraic%20World%20Engine%20Architecture.pdf

howto build business apps on our game engine:
https://www.linkedin.com/pulse/free-book-gpl3-open-source-building-self-service-helpdesk-jim-ames-ertle/

31 jan 2026

features:

-speech out of descriptions / gameplay
- player to player CHAT with TELL command
- multi user
- SSH multi player
- player vs player
- auto spawning demons, trolls and bosses
- health and hit points
- magic potions
- physics for ice and water

to run system:

you will need two venv for python:
-------------------------------------
Create venv for voice
mkdir voice
cd voice
python -m venv venv_voice
venv_voice\scripts\activate

put the ssh_voice_simple.py in the voice folder

--------------------------------------------------
Create venv for server
mkdir server
cd server
python -m venv venv_server
venv_server\scripts\activate

put the ssh_server_multiplayer_rpg.py in the server folder with ALL the files from the repo

make a config dir
put all the .ini in folder config

- be SURE to make a config folder and put all the .ini in config folder...inside the server folder

--------------------------------------------------------------------------

  



start talking server:                python ssh_server_multiplayer_rpg.py - be sure to make a new venv and run this cmd in there first time: pip install -r requirements.txt

start SSH clients - no sound:               ssh -p 2222 player@localhost (or ip of zorksshserver)

---------------------------------------------------------------
start speech enabled client: python ssh_voice_simple.py  - be sure to make a new venv and run this cmd in there first time: pip install -r voice-client-requirements.txt

---------------------------------------------------------------------

start CHAT enabled server:   python speech_ssh_server.py

start CHAT enabled client:    python chat_ssh_client.py


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



🎯 CLEANER VERSION FOR README:
markdown# 🚀 ZORK RPG - Installation Guide

## 📦 Prerequisites
- Python 3.8+
- Windows 10/11 (or Mac/Linux)
- OpenSSH client installed

---

## 🎮 Option 1: Voice-Enabled Client (Recommended!)

### Setup:
```cmd
# 1. Create voice client folder
mkdir voice
cd voice

# 2. Create virtual environment
python -m venv venv_voice
venv_voice\Scripts\activate

# 3. Install dependencies (first time only)
pip install -r voice-client-requirements.txt

# 4. Copy files here:
#    - ssh_voice_simple.py
#    - voice-client-requirements.txt
```

### Run:
```cmd
cd voice
venv_voice\Scripts\activate
python ssh_voice_simple.py
```

**Or connect to remote server:**
```cmd
python ssh_voice_simple.py --host 192.168.1.100
```

---

## 🖥️ Option 2: Standard SSH Client (No Voice)
```cmd
ssh -p 2222 player@localhost
```

**Or connect to remote server:**
```cmd
ssh -p 2222 player@192.168.1.100
```

---

## 🌐 Server Setup

### Setup:
```cmd
# 1. Create server folder
mkdir server
cd server

# 2. Create virtual environment
python -m venv venv_server
venv_server\Scripts\activate

# 3. Install dependencies (first time only)
pip install -r requirements.txt

# 4. Create config folder
mkdir config

# 5. Copy files:
#    Server folder:
#      - ssh_server_multiplayer_rpg.py
#      - game_engine_rpg.py
#      - requirements.txt
#
#    Config folder (inside server):
#      - rooms.ini
#      - objects.ini
#      - verbs.ini
#      - combat.ini
#      - sprites.ini
#      - transformations.ini
```

### File Structure:
```
server/
├── ssh_server_multiplayer_rpg.py
├── game_engine_rpg.py
├── requirements.txt
├── venv_server/
└── config/
    ├── rooms.ini
    ├── objects.ini
    ├── verbs.ini
    ├── combat.ini
    ├── sprites.ini
    └── transformations.ini
```

### Run:
```cmd
cd server
venv_server\Scripts\activate
python ssh_server_multiplayer_rpg.py
```

---

## 🎯 Quick Start (Complete Demo)

### Terminal 1 - Start Server:
```cmd
cd server
venv_server\Scripts\activate
python ssh_server_multiplayer_rpg.py
```

### Terminal 2 - Player 1 (Voice):
```cmd
cd voice
venv_voice\Scripts\activate
python ssh_voice_simple.py
```

### Terminal 3 - Player 2 (Voice):
```cmd
cd voice
venv_voice\Scripts\activate
python ssh_voice_simple.py
```

**Both players can now see each other and hear voice on their own speakers!** 🔊

---

## 📝 Requirements Files

**voice-client-requirements.txt:**
```txt
pyttsx3
```

**requirements.txt (server):**
```txt
asyncssh
```

---

## 🎮 In-Game Commands
```
Movement:  north/n, south/s, east/e, west/w
Actions:   look/l, examine [obj], take [obj], drop [obj], inventory/i
Combat:    attack [enemy], attack [enemy] with [weapon], flee
PvP:       pvp (toggle), attack [player], stats
Social:    say [message], who (list players)
Meta:      help, voice (toggle), quit
```

---

## ⚠️ Important Notes

- ✅ **MUST** create `config/` folder inside `server/` folder
- ✅ **MUST** put all `.ini` files in `config/` folder
- ✅ Run `pip install -r requirements.txt` first time only
- ✅ Server must be running before clients connect
- ✅ Voice works on each client's local speakers (no audio streaming!)

---

## 🔧 Troubleshooting

**"Connection refused"**
- Make sure server is running first
- Check firewall settings

**"No module named asyncssh"**
- Activate venv: `venv_server\Scripts\activate`
- Install: `pip install -r requirements.txt`

**"No voice"**
- Type `voice` in game to toggle
- Check: `pip install pyttsx3`

**"Config files not found"**
- Make sure `config/` folder exists in `server/` folder
- Copy all `.ini` files to `config/` folder

---

## 🎉 That's It!

Enjoy the game! 🎮🔊

🎯 EVEN SIMPLER VERSION (For Less Technical Users):
markdown# 🎮 ZORK RPG - Quick Setup

## 🔊 Voice Client Setup:

1. **Create folder and setup:**
```cmd
   mkdir voice
   cd voice
   python -m venv venv_voice
   venv_voice\Scripts\activate
   pip install pyttsx3
```

2. **Copy these files to `voice` folder:**
   - `ssh_voice_simple.py`

3. **Run client:**
```cmd
   python ssh_voice_simple.py
```

---

## 🌐 Server Setup:

1. **Create folder and setup:**
```cmd
   mkdir server
   cd server
   python -m venv venv_server
   venv_server\Scripts\activate
   pip install asyncssh
   mkdir config
```

2. **Copy these files to `server` folder:**
   - `ssh_server_multiplayer_rpg.py`
   - `game_engine_rpg.py`

3. **Copy these files to `server/config` folder:**
   - `rooms.ini`
   - `objects.ini`
   - `verbs.ini`
   - `combat.ini`
   - `sprites.ini`
   - `transformations.ini`

4. **Run server:**
```cmd
   python ssh_server_multiplayer_rpg.py
```

---

## ✅ Done!

Connect clients to your server and enjoy multiplayer voice RPG! 🎉

💡 SUGGESTIONS:

✅ Your instructions are CORRECT!
📝 Maybe add the file structure diagram (helps visual learners)
🎯 Consider splitting into "Quick Start" vs "Detailed Setup"
📋 Add a troubleshooting section
🔥 Emphasize the config folder (that's the #1 mistake users will make!)

---

Built to demonstrate the power of algebraic game design 🎮
