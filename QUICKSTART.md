# ⚡ Quick Start Guide

Get up and running in 2 minutes!

---

## 🎯 Option 1: Fastest Start (Terminal Play)

```bash
cd zork_game
./setup.sh
./run_game.py
```

That's it! You're playing!

---

## 🌐 Option 2: SSH Server Mode

```bash
cd zork_game
./setup.sh
./ssh_server.py
```

Then from another terminal:
```bash
ssh -p 2222 player@localhost
```

---

## 🎮 Your First Game Session

Try these commands to see the water→ice demo:

```
> look
> go west
> take water
> go north
> drop water
> wait
> wait
> wait
> examine water
```

**BOOM!** The water has frozen into ice! ❄️

---

## 📚 What to Read Next

### For Playing:
- Type `help` in the game
- See `DEMO_WALKTHROUGH.md` for detailed commands

### For Learning:
- `README.md` - Architecture overview
- `ARCHITECTURE.md` - Deep technical dive
- `DIAGRAMS.md` - Visual explanations
- `PRESENTATION.md` - Team demo guide

### For Verifying:
```bash
./test_game.py
```
Runs automated tests to verify everything works.

---

## 🔧 Common Commands

**In-Game:**
- `look` - Look around
- `examine <thing>` - Look closely at something
- `take <thing>` - Pick up an item
- `go <direction>` - Move (north, south, east, west, up, down)
- `inventory` or `i` - Show what you're carrying
- `wait` - Pass time (advance turn counter)
- `save <name>` - Save your game
- `load <name>` - Load a saved game
- `quit` - Exit

**Directions:**
- `n`, `s`, `e`, `w`, `u`, `d` (shortcuts)
- `north`, `south`, `east`, `west`, `up`, `down` (full names)

---

## 🎓 Demo This to Your Team

1. **Show the config files** (`config/*.ini`)
   - Point out how simple they are
   - They're just data!

2. **Run the water→ice demo**
   - Follow `DEMO_WALKTHROUGH.md`
   - Show the transformation happen live

3. **Open the code** (`game_engine.py`)
   - Show how small it is (~400 lines)
   - Point out the matrix check (one line!)

4. **Try adding content**
   - Add a new object to `objects.ini`
   - No code changes needed!

5. **Run the tests**
   - `./test_game.py`
   - Show everything works automatically

---

## 🚀 Next Steps

### Extend the Game:

1. **Add a new object**
   Edit `config/objects.ini`:
   ```ini
   [torch]
   name = burning torch
   description = A torch with flickering flames
   location = entrance_hall
   takeable = true
   valid_verbs = take, drop, examine, use
   ```

2. **Add a new room**
   Edit `config/rooms.ini`:
   ```ini
   [dungeon]
   name = Dark Dungeon
   description = A damp, dark cell
   north = entrance_hall
   ```

3. **Add a new transformation**
   Edit `config/transformations.ini`:
   ```ini
   [ice_melts]
   object_id = ice
   turns_required = 5
   new_object_id = water
   message = The ice has melted!
   ```

### Share with Team:

1. Commit to your repo
2. Share the link
3. Schedule a 30-min demo
4. Use `PRESENTATION.md` as your guide

---

## 🆘 Troubleshooting

**Problem:** Game won't start
```bash
# Make sure scripts are executable
chmod +x run_game.py ssh_server.py setup.sh test_game.py
```

**Problem:** Missing dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

**Problem:** SSH won't connect
```bash
# Generate host key
ssh-keygen -t rsa -f ssh_host_key -N ""
```

**Problem:** Tests fail
```bash
# Check config files exist
ls config/
# Should see: verbs.ini, objects.ini, rooms.ini, transformations.ini
```

---

## 💡 Tips

1. **Start simple** - Run `./run_game.py` first
2. **Read the code** - It's designed to be readable!
3. **Modify the config** - Safe to experiment
4. **Run tests often** - `./test_game.py` catches issues
5. **Show your team** - This is a great teaching tool!

---

## 📁 File Reference

```
zork_game/
├── 📄 README.md              ← Start here
├── ⚡ QUICKSTART.md          ← This file
├── 🎮 DEMO_WALKTHROUGH.md   ← Step-by-step demo
├── 🏗️ ARCHITECTURE.md        ← Technical details
├── 🎨 DIAGRAMS.md            ← Visual explanations
├── 🎤 PRESENTATION.md        ← Team demo guide
├── 🐍 game_engine.py         ← Core logic
├── 🖥️ run_game.py            ← Terminal interface
├── 🌐 ssh_server.py          ← SSH server
├── 🧪 test_game.py           ← Automated tests
├── ⚙️ setup.sh               ← Setup script
└── 📂 config/                ← Game data
    ├── verbs.ini
    ├── objects.ini
    ├── rooms.ini
    └── transformations.ini
```

---

## 🎯 Success Criteria

You'll know you're ready to demo when:

✅ `./test_game.py` shows all tests passing
✅ You can play through the water→ice demo
✅ You understand the matrix concept
✅ You can explain why it's better than if/else
✅ You're excited to show your team!

---

**Ready? Let's go!** 🚀

```bash
./run_game.py
```

Have fun exploring! 🎮
