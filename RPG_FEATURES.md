# ZORK RPG - NEW FEATURES! 🎮⚔️

## What's New:

### 💚 Health System
- Start with 100 HP
- Lose 2 HP every 5 turns (hunger/exhaustion)
- Find and drink potions to heal!
- Die if health reaches 0

### 🗡️ Combat System
- **Attack enemies:** `attack troll` or `attack troll with sword`
- Weapons do bonus damage (sword: 20, axe: 30, knife: 15, rock: 8)
- Enemies have HP bars: [████░░░░] 40/80 HP
- **Flee from combat:** `flee` or `run`

### 👹 Sprites/NPCs
- **Trolls:** 50 HP, 15 damage - aggressive, pick up items!
- **Goblins:** 25 HP, 8 damage - item thieves
- **Shadow Demons:** 100 HP, 25 damage - always hostile!
- **Giant Rats:** 15 HP, 5 damage - scavengers
- **Boss Dragon:** 200 HP, 40 damage - epic fight!

### 🎲 Procedural Spawning
- Enemies spawn randomly around the world
- Health potions appear in random rooms
- Sprites can pick up weapons (watch out!)
- Each spawn has random stats

### 💊 Consumables
- **Red Potion:** +30 HP (spawns frequently)
- **Mega Potion:** +75 HP (rare!)
- **Antidote:** +10 HP, cures poison
- Use: `drink potion`

### ⚔️ Weapons
- **Battle Axe:** 30 damage (in secret room!)
- **Rusty Sword:** 20 damage (entrance hall)
- **Kitchen Knife:** 15 damage (kitchen)
- **Club:** 12 damage (sprites drop these)
- **Rock:** 8 damage (courtyard)

### 🧊 Physics (Enhanced)
- **Water → Ice:** Drop water in freezer, wait 3 turns
- **Ice → Water:** Take ice to warm room, wait 3 turns (NEW!)

## How to Play:

```bash
# Single player RPG mode
python run_game_rpg.py

# Commands
look                    # See room, enemies, items
health                  # Check your HP
attack troll            # Attack with any weapon you're holding
attack demon with sword # Attack with specific weapon
drink red potion        # Heal yourself
flee                    # Run to random exit
inventory               # See what you're carrying
```

## Example Combat Session:

```
> look

Kitchen
=======
An old medieval kitchen...

🚨 ENEMIES:
  ⚔️  brutal troll [█████░░░░░] 50/50 HP (holding: club)

You can see:
  ⚔️  kitchen knife
  - moldy cheese

> take knife
Taken: kitchen knife

> attack troll with knife
⚔️  You attack the brutal troll with kitchen knife for 20 damage! (30/50 HP remaining)

⚔️  The brutal troll attacks you for 15 damage!

> attack troll with knife
⚔️  You attack the brutal troll with kitchen knife for 20 damage! (10/50 HP remaining)

> attack troll with knife
⚔️  You attack the brutal troll with kitchen knife for 20 damage!
💀 The brutal troll has been slain!
💰 The brutal troll dropped: club
```

## Multiplayer File Structure:

```
game_world/          ← Can be SharePoint mapped drive!
├── world/           (Shared config - read-only)
│   ├── rooms.ini
│   ├── objects.ini
│   ├── sprites.ini
│   └── world_state.json
└── players/         (Individual states)
    ├── jim.json     (health, inventory, location)
    ├── bob.json
    └── alice.json
```

**Each player:**
- Reads from shared `world/` directory
- Writes ONLY to their own `players/name.json`
- No file conflicts!
- Works on SharePoint via mapped drive

## Stats Tracked:

- Turns survived
- Enemies killed
- Times died
- Potions consumed
- Damage dealt
- Damage taken

## Try These Challenges:

1. **Survival Run:** How many turns can you survive?
2. **Dragon Slayer:** Find and defeat the ancient dragon!
3. **Pacifist:** Collect all weapons without killing anything
4. **Speedrun:** Get to secret room in under 20 turns
5. **Weapon Master:** Kill one enemy with each weapon type

## Coming Next (Friday):

- 🌐 **SSH Multiplayer** - Multiple players in same world!
- 👥 **Player Visibility** - See other players in rooms
- 💬 **Communication** - Say commands to talk to others
- 🤝 **Trading** - Give items to other players
- 🏆 **Leaderboards** - Compare stats across players

---

**Ready to play? Run:**
```bash
python run_game_rpg.py
```

**Tips:**
- Pick up weapons immediately!
- Keep a potion in inventory at all times
- Don't let sprites get the good weapons
- Flee if health drops below 30
- The freezer is cold... and dangerous 🧊

Have fun! ⚔️🎮
