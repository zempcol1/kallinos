# Kallinos — Game Design

A 2D turn-based RPG set in a loosely historical Ancient Greece. Kallinos, a
scrawny nobody from a coastal village, rises through trials and battles to
become a legend, and finally discovers he may be more than mortal.

---

## Pillars

- **From nobody to god.** The power curve is the story: a stick-wielding
  teenager in Act I, a candidate for godhood in Act IV.
- **Grounded first, mythic later.** Act I is small, warm and a little funny
  (the first enemy is a big frog). The gods stay deniable at first and then
  step forward act by act.
- **Greece you can feel.** Olive groves, whitewashed houses, terracotta roofs,
  painted temples, the sea. Myth is woven into the everyday.
- **Readable, snappy combat.** GBC/GBA-style 1v1 turns with real depth, but
  never slow.

## Key decisions

| Topic       | Decision                                                                 |
|-------------|--------------------------------------------------------------------------|
| Scope now   | A polished **Act I vertical slice** (~1–2h) before widening.             |
| Story       | Mostly linear; choices add flavor and feed **2–3 endings**.              |
| Combat      | **1v1** turn-based, deepened with skills, a resource bar, types and status effects. |
| World       | Act I = connected maps (doors, map edges). Act II overworld: undecided.  |
| Art         | **Hybrid**: procedural code art for tiles/scenery, hand-drawn PNGs for characters, portraits, bosses. Code art is always the fallback. |
| Audio       | Generated in code for now; may be replaced by asset files later.         |
| Content     | **Data-driven**: maps, dialogue, cutscenes and quests live in JSON.      |

---

## Story

### Act I — The Nobody (levels 1–10)
1. **Tutorial: the garden** *(implemented)*. Niko vanishes behind a boulder;
   Kallinos grabs a fallen olive branch and fights a cat-sized frog. The olive
   tree shimmers.
2. **Next morning.** Errands around Kyrillos teach the village, the shop and
   side quests. Strange soldiers at the harbor.
3. **Elder Theron** asks about the branch: *"Athena's tree does not drop its
   branches for just anyone."*
4. **Growing up.** Small quests teach combat depth: a boar in the grove, crabs on
   the shore, Niko's dare in the sea cave (first dungeon).
5. **Unease.** The "merchants" are raiders. Optional clues can be found.
6. **The Raid.** A night attack; Kyrillos burns. An escape through the village,
   forced fights, and a flavor choice of whom to help first.
7. **Boss: the raider captain** at the temple. Mid-fight the branch glows: the
   first divine moment, never explained.
8. **Aftermath.** Theron, wounded or taken, leaves a fragment: *"Your mother was
   not the only one who prayed for you."*
9. **Departure** along the coastal road.

### Act II — The Warrior's Path (levels 11–25)
Travel the city-states (Athens, Sparta, Corinth, Delphi), one per chapter, each
with a trial, a boss and a new ally or skill. Mythic creatures (harpies,
cyclopes, minotaurs) mix with human enemies. Key beats: betrayal by a mentor,
alliance with a demigod, a prophecy at Delphi. Reveal who sponsored the raid.

### Act III — The Legend (levels 26–40)
Leading armies and choosing between city-states, interference from the
Olympians, a descent into the Underworld, and a climax against a Titan or a
corrupted god.

### Act IV — Apotheosis (level 40+)
The twist: Kallinos is of divine lineage, foreshadowed since the tutorial.
Trials of ascension, one per Olympian domain, then the ending.

### Endings (draft)
Decided by a few big choices in Acts III/IV plus a hidden **mortal bonds**
score (people helped, companions kept alive):
- **Apotheosis**: accept godhood and become a new god of something earned in play.
- **The Mortal Choice**: refuse divinity and go home to rebuild Kyrillos.
- **The Usurper** *(optional, dark)*: seize power from a corrupted Olympian.

### Threads seeded in Act I
- **The olive branch** (Athena's sacred tree) grows into a real weapon over the game.
- **Leto's frog curse.** Frogs near olive trees are said to be Lycian peasants
  Leto cursed. Frogs keep reappearing (secret boss, later Leto herself).
- **Theron's secret** about Kallinos' parentage.
- **The raiders' sponsor** is a city-state or a god.

### Cast (Act I)
| Name          | Role                                                           |
|---------------|----------------------------------------------------------------|
| Kallinos      | The player. Scrawny teenager, no combat experience.            |
| Doros         | Talkative friend, cautious, provides commentary.               |
| Niko          | Bold friend, dares others, gets into trouble.                  |
| Elder Theron  | Village elder and temple keeper; knows more than he says.      |

---

## Gameplay

### Core loop
```
Explore → meet NPCs / events → dialogue or combat → XP, items, story flags → explore
```

### Exploration
- Tile maps, 16px tiles at 3× scale; free movement with collision boxes.
- Interact (E/Enter) with NPCs, items, doors and signs.
- Maps connect through doors and map edges; interiors are small maps.
- Visible roaming enemies rather than random battles *(leaning; not final)*.

### Combat
- 1v1 turns: **Attack, Defend, Item, Flee**, plus **Skills** (planned).
- Damage: `attack + weapon_bonus - defense + variance`, min 1. Defend halves
  the next hit.
- Planned depth:
  - **Menos** (μένος, battle fury): a bar that fills when hitting or getting
    hit, spent on skills.
  - **Types**: Mortal, Beast, Monster, Undead, Divine (small chart).
  - **Status effects**: poison, bleed, stun, slow, blessed, cursed.
  - **Enemy move lists** with weights/conditions; speed, crits, misses.
  - **Multi-phase bosses** (new moves, sprite swap, dialogue).
- Defeat leads to a Game Over screen and retry from the last checkpoint.

### Progression & items
- XP → level up → stat growth and skill unlocks.
- Slots: weapon, armor, accessory. Categories: weapons, armor, consumables,
  quest items. Currency: drachma, spent at the agora shop.
- Act I item ideas: figs, bread, olive oil, honey, wine, sling, bronze knife,
  leather cuirass, Athena's owl charm.

### Quests & story state
- Global story flags drive everything: NPC dialogue variants, map changes
  (e.g. burning Kyrillos), quest stages, endings.
- Quest log plus an active-quest tracker on the HUD.

### Act I world
House (interior), garden *(done)*, Kyrillos village *(started)*, Temple of
Athena, agora, harbor, olive grove & hills, marsh, sea cave (dungeon), burning
Kyrillos (raid variant), coastal road.

Act I enemies: Vátrachos *(done)*, wild boar, goat, crab swarm, sea snake,
bandit, bandit archer, raider hoplite. Bosses: raider captain; secret boss
"Mother of Frogs".

---

## Tutorial reference *(implemented)*

**Setting:** a fenced garden behind a house on the edge of Kyrillos, late
afternoon, golden light. Landmarks: house, stone walls, fence, a mossy boulder
beside a gnarled olive tree (Athena's), a fallen olive-wood branch.

**Vátrachos (Βάτραχος):** a cat-sized marsh frog with amber eyes. Not a
monster, just a very big frog. HP 18 · ATK 4 · DEF 1 · 10 XP.

**Olive-Wood Branch:** `olive_branch`, weapon, +2 attack. A quiet divine seed.

**Beats:** fade in → Niko investigates the boulder and vanishes → *croak* →
player explores → picks up the branch (auto-equips; the boulder is blocked
without it) → frog reveal → combat (flee locked) → frog hops away → Niko drops
from the tree → the olive tree shimmers → "Tutorial Complete" → village.

---

## Art direction

### Style
- 16-bit pixel art, SNES / GBA RPG feel. Top-down 3/4 view for exploration;
  side view for combat.
- **Logical sizes:** tiles 16×16, characters 16×24 (4 directions × 4 walk
  frames), scaled 3× (48px tiles); combat sprites 6×.
- 1px dark outline on characters and props; light from the top-left.
- **Hybrid pipeline** *(planned)*: a PNG in `assets/images/` overrides the procedural
  sprite of the same id. PNG candidates: main cast, dialogue portraits, bosses.
  Character sheets use rows down/up/left/right and 4 columns of 16×24.

### World look
- Whitewashed plaster, terracotta roofs, silvery-green olive trees, cypresses,
  vines, marble columns. Painted temples: blue and gold accents.
- Underworld: dark stone, green/blue ghost light. Olympus: white, gold, clouds.
- Planned: water and shoreline, animated tiles, time-of-day tint (golden
  afternoon, night raid), fire glow, particles (dust, leaves, embers).

### Palette
| Role        | Hex       | Role            | Hex       |
|-------------|-----------|-----------------|-----------|
| Sand        | `#E8D5A3` | Menu BG         | `#0F0F23` |
| Olive green | `#6B8E4E` | Combat BG       | `#1A1A2E` |
| Deep sea    | `#1B4F72` | Panel blue      | `#16213E` |
| Sky blue    | `#85C1E9` | Accent gold     | `#D4A844` |
| Terracotta  | `#C0725E` | Title gold      | `#F1C40F` |
| Marble      | `#F2EFEA` | HP red          | `#C0392B` |
| Stone       | `#8D8D8D` | MP blue         | `#2980B9` |
| Dark wood   | `#5D4037` | XP green        | `#27AE60` |

**Meaning:** gold = selected/important, red = damage, green = healing,
blue = information/mana.

### Animation
| Animation        | Timing                                             |
|------------------|----------------------------------------------------|
| Walk cycle       | 4 frames × 150ms                                   |
| Enemy idle       | 2 frames × 600ms                                   |
| Attack lunge     | 240ms                                              |
| Hit reaction     | white flash + shake, ~320ms                        |
| Enemy defeat     | fade out, 700ms                                    |
| Screen fade      | ~500ms                                             |

### UI
- Translucent dark panels with a gold border; high contrast text.
- Exploration HUD: location bar on top, controls hint on the bottom; planned
  HP and active-quest tracker.
- Combat: enemy upper right with name and HP bar, player lower left, action
  menu bottom right, player panel bottom left, messages above the panels.
- Dialogue: bottom box, speaker name in gold; planned typewriter text,
  portraits and choices.
- Fonts: pygame default for now; planned pixel font (check the license, e.g.
  Press Start 2P, OFL) and a Greek-key (meander) panel border.
- Every input gets visible feedback.

---

## Audio direction
- **Now:** synthesized in code (square/triangle/noise with envelopes) into
  `pygame.mixer.Sound` buffers; no files needed.
- **SFX:** menu, footsteps, hits, crits, heal, level up, pickup, doors, croak,
  text blip.
- **Music:** short looping chiptune tracks (title, village, combat, boss, sad)
  with a lyre-like timbre and Greek modes (Dorian, Phrygian).
- **Later:** may switch to files in `assets/sounds/` behind the same API.
