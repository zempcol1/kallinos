# Kallinos — Engineering Guide

Python 3.12+ (developed on 3.14) and pygame-ce. Game and art design live in
`design.md`. The roadmap is `PLAN.md`: private, gitignored, and may be missing.

## Run

```bash
pip install pygame-ce
python main.py
```

Stand-alone Windows build: `pip install pyinstaller`, then `python build_exe.py`
writes `dist/Kallinos.exe` (one file, assets bundled, app icon from
`icons.app_icon`). When frozen, `settings.BASE_DIR` points into the bundle, so
always build file paths from `settings`, never from the working directory.

Headless (tests, screenshots): set `SDL_VIDEODRIVER=dummy` before importing
pygame, build `Game()`, then drive `game.state_machine` directly by calling
`handle_events`/`update`/`render` on the states and saving `game.screen` with
`pygame.image.save`. There is no test suite yet; pytest with a headless
playthrough test is planned.

## Layout

```
main.py                 Entry point
build_exe.py            Builds dist/Kallinos.exe with PyInstaller
settings.py             All constants: screen, scale, timings, colors, paths
game/
  game.py               Game: window, clock, main loop, registers states, new_game()
  session.py            GameSession: the persistent player + map-entry checkpoint
  state_machine.py      State base class + stack-based StateMachine
states/                 One class per file
  main_menu.py          Animated title screen (sunset scene, logo, menu)
  exploration.py        Generic overworld; delegates story to the map's MapScript
  dialogue.py           Overlay text box: portrait, name tab, typewriter text
  combat.py             1v1 turn-based combat (Attack/Defend/Item/Flee)
  game_over.py          Defeat screen: Retry (checkpoint) / Main Menu
  title_card.py         Full-screen chapter card, then changes to a next state
story/                  Map scripts (story logic per map)
  map_script.py         MapScript base: hooks called by Exploration
  tutorial.py           TutorialScript (data in assets/data/scripts/tutorial.json)
entities/
  character.py          Base for people: feet box, facing, walk cycle, depth, shadow
  player.py, npc.py     Character subclasses (NPCs can walk scripted paths)
  prop.py               Depth-sorted map object (trees, fences...), harvestable
  enemy.py              Combat stats loaded from enemies.json
  item_pickup.py        Bobbing item on the map
systems/
  map_system.py         Loads map JSON: ground layer (+ shadows), props, overhead
  camera.py             Follows the player; centers maps smaller than the screen
  inventory_system.py   Items + equipped weapon
  sprites/              Procedural pixel art (below)
ui/
  widgets.py            font(), draw_panel(), draw_bar(), draw_text_box(), wrap_text(),
                        draw_fade_strip(), draw_shadowed_text(), draw_ornament_rules()
assets/data/            items.json, enemies.json, maps/*.json, scripts/*.json
```

## State machine

- States implement `enter(params)`, `exit()`, `resume()`, `handle_events(events)`,
  `update(dt)` and `render(surface)`. `dt` is in milliseconds.
- `push` adds an overlay (dialogue, combat), `pop` returns to the state below
  and calls its `resume()`, and `change` replaces the current state.
- `Game.run` renders the **whole stack** bottom to top, so overlays draw over
  the state beneath them. Only the top state gets events and updates.
- Callbacks back to the state below: `Dialogue` calls
  `on_dialogue_complete(event_id)`, and `Combat` calls `on_combat_victory()`.
  `Dialogue` takes `looks` ({speaker: Look}) to show portraits; Exploration
  fills it from the player and the map's NPCs.
  Combat defeat changes to `game_over`.
- Persistent data (the player) lives in `game.session`, never in a state.
  `Game.new_game()` starts a fresh session. Entering a map takes a checkpoint,
  and Game Over → Retry restores it.
- New state: create `states/x.py`, then register it in `Game.__init__`.

## Map scripts (`story/`)

`Exploration` is generic. Story logic for a map lives in a `MapScript`
subclass, chosen by the map's `"script"` key via `story.MAP_SCRIPTS`. Hooks:
`on_start`, `allows_control`, `update`, `on_dialogue_complete`,
`on_combat_victory`, `render`. Scripts act through Exploration's helpers:
`player`, `tile_map`, `get_npc`, `show_toast`, `push_dialogue(lines,
on_complete)`, `start_combat(enemy_id, can_flee, hint)`, `fade_out(callback)`.
For small cutscenes, NPCs have `walk(path)`/`walking`, and characters have
`lift` (height off the ground) and `alpha`.
Keep text, ids and positions in `assets/data/scripts/<id>.json`, not in Python.
A JSON command runner is planned to replace most script classes.

## Map JSON (`assets/data/maps/*.json`)

All coordinates and sizes are in **tiles** (fractions allowed for
collisions and triggers).

| Key            | Meaning                                                          |
|----------------|------------------------------------------------------------------|
| `name`, `display_name` | id / text shown in the HUD location bar                  |
| `script`, `intro_toast` | optional MapScript id / toast shown after fade-in       |
| `width`, `height`, `player_start` | size and spawn tile                           |
| `ground`       | rows of tile ids: `0` grass, `1` dirt path (auto-edged)          |
| `objects`      | `{type, x, y, w, h, variant?, id?, solid?, harvest?, harvest_text?}`; see below |
| `collisions`   | `{x, y, w, h}` extra blocking rects (walls, houses)              |
| `triggers`     | `{id, x, y, w, h}` zones checked by state code                   |
| `npcs`         | `{id, name, x, y, color, hair?, hair_style?, trim?, bearded?, dialogue_idle[]}` |
| `item_pickups` | `{item_id, x, y, color}` (color = fallback when no sprite)       |

Objects (`OBJECT_TYPES` in `systems/sprites/objects.py`):

- **Ground** (baked under characters): `house_wall`, `house_roof`,
  `house_door`, `temple`, `stone_wall` (terrace wall; on tall walls the top
  stays transparent so the grass reads as the bank behind it).
- **Sorted** (props, depth-sorted with characters, so you can walk behind
  them): `olive_tree` (3×3), `cypress` (2×4), `plane_tree` (5×5), `fig_tree`
  (3×3 tree, 2×2 bush), `bush` (variants 0 myrtle, 1 oleander, 2 lavender),
  `boulder`, `fence`. Trees fade while the player stands behind them.
- `fence` is tiled: every fence tile links to its fence neighbours, so
  overlapping runs form clean corners, ends and junctions.
- Sorted objects get an automatic collision **footprint** (trunk base, rails);
  `"solid": false` turns it off. Their shadows are baked into the ground.
- `variant` reseeds or restyles the sprite; `id` lets scripts find the prop
  (`tile_map.get_prop(id)`); `harvest: item_id` (fig trees) gives that item
  once on interact, then shows the picked sprite. Later entries draw on top.

## Sprites (`systems/sprites/`)

Everything is generated in code at logical size and scaled by
`settings.SCALE`. Generators are `@cached`, so calling them every frame is free.

| Module          | Contents                                                         |
|-----------------|------------------------------------------------------------------|
| `pixel_art.py`  | `from_grid`, `mirrored`, `stamp`, `outline`, `silhouette`, `shade`, `lerp`, `seeded`, `cached` |
| `tiles.py`      | Ground tiles (grass, dirt path)                                  |
| `structures.py` | Houses, terrace stone wall, fence pieces, temple                 |
| `nature.py`     | Olive, cypress, plane and fig trees, bushes, boulder             |
| `objects.py`    | `OBJECT_TYPES`: per type the sprite, layer, footprint and shadow |
| `characters.py` | People: shared body grids + hair-style overlays, colored by a `Look` |
| `portraits.py`  | 32×32 dialogue busts from a `Look` (talking/blinking frames)     |
| `creatures.py`  | Enemies by id (`ENEMY_GENERATORS`, `ENEMY_IDLE_FRAMES`)          |
| `items.py`      | Items by id (`ITEM_GENERATORS`)                                  |
| `icons.py`      | Small UI sprites: interact bubble, continue arrow, laurel, app icon |
| `backdrops.py`  | Full-screen combat backdrop                                      |
| `title.py`      | Title screen layers (sky, sea, headland, olive) and the logo     |

- **Hand-drawn** sprites are text grids, one character per pixel, mapped
  through a palette; `.` is transparent. For symmetric sprites, store the left
  half and use `mirrored()`. `from_grid` raises on ragged rows.
- **Procedural** sprites use `seeded(...)` RNGs so every run looks the same.
- Light comes from the top-left; shadows fall to the bottom-right in one
  translucent shadow color (`TileMap.SHADOW_COLOR`).
- **New object:** add `def thing(w, h, variant=0)` to `structures.py` or
  `nature.py`, plus a footprint/shadow function if it is sorted, and register
  an `ObjectType` in `OBJECT_TYPES`.
- **New NPC look:** set `color`, `hair`, `hair_style` (`short`, `tousled`,
  `curly`, `elder`), `trim` and `bearded` in the map JSON. The same `Look`
  drives the map sprite and the dialogue portrait. A new hair style needs map
  overlays in `characters._HAIR` and a portrait overlay in `portraits._HAIR`.
- **New enemy or item:** add a generator and register it. Unknown ids get a
  placeholder (enemies) or the `color` fallback (items).
- Palettes are defined in the sprite modules; UI colors are in `settings.py`.

## Conventions

- Imports: stdlib, then pygame, then local (`import settings as s`), with
  groups separated by a blank line. No wildcard imports.
- `snake_case` files/functions, `PascalCase` classes, `UPPER_SNAKE` constants,
  `_private` members, `snake_case` JSON keys.
- Line length up to 100. Google-style docstrings on classes and non-obvious
  public methods. Match the surrounding comment density.
- No magic numbers in logic: put them in `settings.py` or named locals/class
  constants.
- Error handling only at boundaries (file I/O, asset loading).
- One `pygame.display.set_mode` (in `Game`); states never call `flip()`.
  Multiply movement and timers by `dt`.
- Draw UI through `ui/widgets.py`, and get fonts from `font(size)`; don't
  create fonts per frame.
- Content (maps, items, enemies, and later dialogue/scripts/quests) belongs in
  JSON, not Python.

## Git

- Short, imperative commit messages ("Add boar enemy"). Same for PR titles
  and bodies.
- No AI/Claude attribution in commits or PRs.
- Work on a branch, open a PR to `main`, merge.
