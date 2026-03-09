# Kallinos — Game Requirements

## Overview

**Kallinos** is a 2D RPG set in a loosely historically accurate Ancient Greece. The player begins as an unknown, weak young Greek citizen and rises through trials, battles, and story events to become a legendary warrior — and ultimately, in a dramatic twist, ascends to godhood.

Built with **Python 3.12+** and **Pygame 2.x**, the game follows a **State Machine architecture** for clean separation of game phases.

---

## Story Arc

### Act I — The Nobody (Levels 1–10)
- Player starts in a small coastal village (e.g., inspired by a minor polis).
- Introduced to basic movement, dialogue, and inventory through mundane tasks.
- First combat encounters: wild animals, petty bandits.
- Inciting incident: the village is attacked or a loved one is taken, pushing the player outward.

### Act II — The Warrior's Path (Levels 11–25)
- Player travels across Greek city-states (Athens, Sparta, Corinth, Delphi, etc.).
- Joins a warband or competes in athletic/combat trials.
- Encounters mythological creatures (harpies, cyclopes, minotaurs) blended with human enemies.
- Gains reputation; NPCs begin recognizing the player.
- Key story beats: betrayal by a mentor, alliance with a demigod, a prophecy revealed at Delphi.

### Act III — The Legend (Levels 26–40)
- Player leads armies, makes political choices between city-states.
- Mythological stakes rise: interference from Olympian gods.
- Descent into the Underworld as a major dungeon/story arc.
- Climactic battle against a Titan or corrupted god.

### Act IV — Apotheosis (Level 40+)
- Plot twist: the player *is* of divine lineage (foreshadowed in Acts II/III).
- Trials of ascension — one for each major Olympian domain.
- Final transformation: the player becomes a new God.
- Epilogue: the player's mortal companions react; the world changes.

---

## Core Gameplay Loop

```
Explore World → Encounter Events/NPCs → Enter Combat or Dialogue
     ↑                                           ↓
     ← Gain XP / Items / Story Progress ←────────┘
```

1. **Exploration:** Tile-based or free-movement 2D maps. Enter buildings, dungeons, cities.
2. **Dialogue & Story:** NPC interactions drive quests and lore. Branching choices where meaningful.
3. **Turn-Based Combat:** Triggered by encounters. Harry Potter GBC/GBA-style:
   - Player and enemy take turns.
   - Actions: Attack, Defend, Use Item, Special Ability, Flee.
   - Elemental/type advantages (e.g., fire vs. ice, divine vs. undead).
4. **Inventory & Equipment:** Collect weapons, armor, consumables, quest items. Equip gear to change stats.
5. **Progression:** XP → Level Up → Stat increases + ability unlocks.

---

## Planned Systems

### 1. State Machine
All game phases are discrete states managed by a central `StateMachine`:
- `MainMenu`
- `Exploration`
- `Combat`
- `Dialogue`
- `Inventory`
- `PauseMenu`
- `GameOver`
- `Cutscene`

### 2. Map / Level System
- Levels defined as data files (JSON or TMX via Tiled).
- Each map has layers: ground, objects, collisions, triggers.
- Transitions between maps via trigger zones (doors, paths).

### 3. Entity System
- **Player:** Stats (HP, MP, STR, DEF, AGI, WIS), level, XP, equipment slots, ability list.
- **NPCs:** Dialogue trees, shop inventories, quest-giver flags.
- **Enemies:** Stats, AI behavior, loot tables, elemental type.

### 4. Inventory & Items
- Item categories: Weapons, Armor, Consumables, Quest Items, Key Items.
- Each item: `id`, `name`, `description`, `type`, `effects`, `icon`.
- Inventory has weight or slot limits.
- Equipment directly modifies player stats.

### 5. Turn-Based Combat
Inspired by Harry Potter GBC/GBA:
- Separate combat screen with player sprite vs. enemy sprite.
- Action menu: Attack | Skill | Item | Defend | Flee
- Damage formula: `base_attack + weapon_bonus - enemy_defense + random_variance`
- Skills cost MP; some have elemental properties.
- Status effects: poison, burn, stun, blessed, cursed.
- Boss fights have multiple phases.

### 6. Quest / Story Progression
- Quest log tracks active, completed, and failed quests.
- Flags/variables system for tracking story state globally.
- Main quests gate Act progression; side quests are optional.

### 7. Save / Load
- Serialize game state to JSON.
- Save slots (3–5).
- Auto-save on map transitions.

### 8. Audio
- Background music per map/state (exploration, combat, menu).
- Sound effects for actions (attack, item use, level up, menu navigation).

---

## Technical Requirements

| Requirement         | Detail                                |
|---------------------|---------------------------------------|
| Language            | Python 3.12+                          |
| Engine              | Pygame 2.x                            |
| Resolution          | 800×600 (scalable)                    |
| Target FPS          | 60                                    |
| Architecture        | Finite State Machine                  |
| Data Formats        | JSON for items, quests, dialogue      |
| Map Editor          | Tiled (TMX export) — future           |
| Version Control     | Git                                   |

---

## Milestones

| #  | Milestone                        | Status      |
|----|----------------------------------|-------------|
| 1  | State Machine + Main Menu        | 🔲 Current  |
| 2  | Exploration state + tile map     | 🔲 Planned  |
| 3  | Player entity + movement         | 🔲 Planned  |
| 4  | Basic combat system              | 🔲 Planned  |
| 5  | Inventory + items                | 🔲 Planned  |
| 6  | NPC dialogue system              | 🔲 Planned  |
| 7  | Quest system                     | 🔲 Planned  |
| 8  | Save/Load                        | 🔲 Planned  |
| 9  | Audio integration                | 🔲 Planned  |
| 10 | Act I content                    | 🔲 Planned  |
