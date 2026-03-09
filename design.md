# Kallinos — Game Design Document

## Overview

**Kallinos** is a 2D RPG set in a loosely historically accurate Ancient Greece. The player begins as an unknown, weak young Greek citizen and rises through trials, battles, and story events to become a legendary warrior — and ultimately, in a dramatic twist, ascends to godhood.

Built with **Python 3.14+** and **Pygame-CE 2.x**, the game follows a **State Machine architecture** for clean separation of game phases.

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

1. **Exploration:** Tile-based 2D maps. Enter buildings, dungeons, cities.
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
All game phases are discrete states managed by a central `StateMachine` (stack-based):
- `MainMenu`, `Exploration`, `Combat`, `Dialogue`
- Future: `Inventory`, `PauseMenu`, `GameOver`, `Cutscene`

### 2. Map / Level System
- Levels defined as JSON data files.
- Each map has layers: ground, objects, collisions, triggers.
- Transitions between maps via trigger zones (doors, paths).

### 3. Entity System
- **Player:** Stats (HP, ATK, DEF, level), equipment slots, ability list.
- **NPCs:** Dialogue, visibility flags, interaction rects.
- **Enemies:** Stats, AI behavior, loot tables.

### 4. Inventory & Equipment
- Item categories: Weapons, Armor, Consumables, Quest Items.
- Each item: `id`, `name`, `description`, `type`, `effects`.
- Equipment slots: weapon, armor (future).
- Equipment directly modifies player stats in combat.

### 5. Turn-Based Combat
- Separate combat screen with player sprite vs. enemy sprite.
- Action menu: Attack | Defend | Item | Flee
- Damage formula: `base_attack + weapon_bonus - enemy_defense + random_variance`
- Status effects (future): poison, burn, stun, blessed, cursed.
- Boss fights with multiple phases (future).

### 6. Quest / Story Progression
- Flags/variables system for tracking story state globally.
- Main quests gate Act progression; side quests are optional.

### 7. Save / Load (Future)
- Serialize game state to JSON. Save slots (3–5). Auto-save on map transitions.

### 8. Audio (Future)
- Background music per map/state. Sound effects for actions.

---

## Technical Requirements

| Requirement         | Detail                                |
|---------------------|---------------------------------------|
| Language            | Python 3.14+                          |
| Engine              | Pygame-CE 2.x                         |
| Resolution          | 800×600 (scalable)                    |
| Target FPS          | 60                                    |
| Architecture        | Stack-based Finite State Machine      |
| Data Formats        | JSON for items, maps, dialogue        |
| Tile Size           | 16px logical, 3× scale (48px render)  |
| Version Control     | Git                                   |

---

## Current WIP — Tutorial Level (Act I Opening)

### Scene Design

**Setting:** A small fenced garden behind a modest Greek house, on the edge of the Village of Kyrillos. Late afternoon, golden light. Cicadas buzzing.

**Characters:**
- **Kallinos** — a scrawny teenager, no combat experience.
- **Doros** — talkative, stays visible, provides commentary.
- **Niko** — the bold one, dares others, goes missing.

**Key landmarks:** House (top), low stone wall/fence, garden with trampled grass, moss-covered boulder next to a gnarled olive tree (Athena's sacred tree), fallen olive-wood branch on the ground.

### The Creature — Vátrachos (Βάτραχος)

A **cat-sized marsh frog** with slick dark-green skin and unsettling amber eyes. Not a monster — just an abnormally large frog. To three teenagers, it's terrifying.

**Mythological flavor:** Local villagers whisper that frogs near old olive trees are cursed — remnants of Lycian peasants whom Leto transformed into frogs for refusing her water.

| Stat     | Value | Rationale                              |
|----------|-------|----------------------------------------|
| HP       | 18    | Dies in ~4–5 hits from a stick         |
| Attack   | 4     | Stings but won't one-shot the player   |
| Defense  | 1     | It's a frog, not armored               |
| XP award | 10    | Just enough to feel rewarding          |

### The First Weapon — Olive-Wood Branch

A **fallen branch from Athena's sacred tree**. Subtle narrative seed — the player unknowingly carries something of faint divine significance.

| Field         | Value                                        |
|---------------|----------------------------------------------|
| id            | `olive_branch`                               |
| name          | Olive-Wood Branch                            |
| type          | weapon                                       |
| attack_bonus  | 2                                            |

### Beat-by-Beat Flow

1. Fade in → garden scene, three friends sitting.
2. Opening dialogue: Niko investigates the boulder, disappears.
3. Croak. Silence. Doros volunteers Kallinos to check.
4. Player gains control, can explore. Doros stays put.
5. Item pickup: olive-wood branch near tree roots. Auto-equips as weapon.
6. Boulder trigger zone: soft-blocked if no branch ("Grab that branch!").
7. Boulder cutscene: fat hissing frog revealed. Lunges.
8. Combat vs. Vátrachos (tutorial fight, flee locked).
9. Victory: frog hops away (stays alive — grounded tone).
10. Post-combat: Niko drops from tree, humorous dialogue.
11. Shimmer on olive tree — foreshadowing.
12. Fade to black → "Tutorial Complete" → transition to Village map.

---

## Implementation Status

### Tutorial Phases

| Phase | Name                        | Status      |
|-------|-----------------------------|-------------|
| 1     | Tile Map & Camera           | ✅ Done     |
| 2     | Player Entity & Movement    | ✅ Done     |
| 3     | NPCs & Dialogue             | ✅ Done     |
| 4     | Inventory & Item Pickup     | ✅ Done     |
| 5     | Trigger Zones & Events      | ✅ Done     |
| 6     | Turn-Based Combat (Basic)   | ✅ Done     |
| 7     | Post-Combat & Wrap-up       | ✅ Done     |
| 8     | Sprite Generation           | ✅ Done     |

### Post-Tutorial

| Feature                              | Status      |
|--------------------------------------|-------------|
| Village map (Act I start)            | ✅ Done     |
| Equipment system (weapon slots)      | ✅ Done     |
| Tutorial → Village progression       | ✅ Done     |

### Future Milestones

| #  | Milestone                        | Status      |
|----|----------------------------------|-------------|
| 1  | Village NPCs & first quest       | 🔲 Planned  |
| 2  | Additional enemy types            | 🔲 Planned  |
| 3  | Expanded combat (skills, items)   | 🔲 Planned  |
| 4  | Quest / flag system               | 🔲 Planned  |
| 5  | Save / Load                       | 🔲 Planned  |
| 6  | Audio integration                 | 🔲 Planned  |
| 7  | Act I content                     | 🔲 Planned  |

---

## Architecture Notes

- **State Machine:** Stack-based FSM. `push()` for overlays (dialogue on top of exploration), `pop()` to resume, `change()` to replace. `resume()` hook prevents re-init on pop.
- **Rendering:** Full stack render — each state on the stack draws in order, so dialogue overlays exploration.
- **Sprites:** Procedurally generated via `systems/sprite_factory.py` — 16×16 tiles, 16×24 characters, scaled 3×.
- **Maps:** JSON files in `assets/data/maps/`. Ground grid + objects + collisions + triggers + NPC/item placement.
- **Exploration:** Supports map-specific scripting (tutorial has phases), generic maps run in free-roam mode.

### File Structure

```
main.py                          # Entry point
settings.py                      # All constants
game/
  game.py                        # Game class, main loop
  state_machine.py               # State + StateMachine
states/
  main_menu.py                   # Title screen
  exploration.py                 # Overworld, tutorial scripting
  dialogue.py                    # Text overlay
  combat.py                      # Turn-based combat
entities/
  player.py                      # Player entity
  npc.py                         # NPC entity
  enemy.py                       # Enemy (combat)
  item_pickup.py                 # World item pickup
systems/
  map_system.py                  # TileMap loader/renderer
  camera.py                      # Camera follow
  inventory_system.py            # Inventory + equipment
  sprite_factory.py              # Procedural sprite generation
assets/data/
  items.json                     # Item definitions
  enemies.json                   # Enemy definitions
  maps/tutorial.json             # Tutorial garden map
  maps/village.json              # Village of Kyrillos map
```
