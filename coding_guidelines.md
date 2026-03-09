# Kallinos — Coding Guidelines

## Repository Structure

```
kallinos/
├── main.py                  # Entry point — initializes and runs the Game
├── settings.py              # Constants: resolution, FPS, colors, paths
│
├── game/                    # Core engine modules
│   ├── __init__.py
│   ├── game.py              # Game class: owns the loop, screen, clock, state machine
│   └── state_machine.py     # StateMachine + base State class
│
├── states/                  # One file per game state
│   ├── __init__.py
│   ├── main_menu.py
│   ├── exploration.py
│   ├── combat.py            # (future)
│   ├── dialogue.py          # (future)
│   ├── inventory.py         # (future)
│   ├── pause_menu.py        # (future)
│   └── game_over.py         # (future)
│
├── entities/                # Player, NPC, Enemy classes
│   ├── __init__.py
│   ├── player.py            # (future)
│   ├── npc.py               # (future)
│   └── enemy.py             # (future)
│
├── systems/                 # Reusable subsystems
│   ├── __init__.py
│   ├── inventory_system.py  # (future)
│   ├── combat_system.py     # (future)
│   ├── quest_system.py      # (future)
│   └── save_system.py       # (future)
│
├── ui/                      # UI components (menus, HUD, text boxes)
│   ├── __init__.py
│   ├── button.py            # (future)
│   ├── text_box.py          # (future)
│   └── hud.py               # (future)
│
├── utils/                   # Pure helper functions
│   ├── __init__.py
│   └── helpers.py           # (future)
│
├── assets/
│   ├── fonts/
│   ├── images/
│   │   ├── characters/
│   │   ├── tilesets/
│   │   ├── ui/
│   │   └── backgrounds/
│   ├── sounds/
│   │   ├── music/
│   │   └── sfx/
│   └── data/                # JSON data files (items, quests, dialogue, maps)
│
├── requirements.md
├── coding_guidelines.md
├── visual_styling.md
└── readme.md
```

**Rule:** Every folder that contains Python modules must have an `__init__.py` (can be empty).

---

## Python & Pygame Best Practices

### General
- **Python version:** 3.12+ (use type hints where they aid clarity).
- **Imports:** Standard library → third-party (`pygame`) → local modules. Separate groups with a blank line.
- **No wildcard imports.** Always `from module import SpecificClass` or `import module`.
- **Keep files focused.** One class per file for states and entities. Utility functions grouped logically.

### Pygame-Specific
- **One `pygame.display.set_mode()` call** in `Game.__init__`. Pass the surface to states.
- **Delta time:** Always pass `dt` (milliseconds from `clock.tick()`) to `update()`. Multiply movement/timers by `dt` for frame-rate independence.
- **Event loop:** Process `pygame.event.get()` once per frame in `Game.run()`, then pass the event list to the active state.
- **Surface blitting:** States receive the display surface and draw onto it. Never call `pygame.display.flip()` inside a state — the Game loop handles it.
- **Asset loading:** Load images/sounds once at startup or state entry, not every frame. Use `convert()` / `convert_alpha()` on loaded images.

---

## Naming Conventions

| Element             | Convention              | Example                        |
|---------------------|-------------------------|--------------------------------|
| Files / modules     | `snake_case.py`         | `main_menu.py`                 |
| Classes             | `PascalCase`            | `StateMachine`, `MainMenu`     |
| Functions / methods | `snake_case`            | `handle_events()`, `update()`  |
| Constants           | `UPPER_SNAKE_CASE`      | `SCREEN_WIDTH`, `FPS`          |
| Private members     | `_leading_underscore`   | `_transitions`, `_stack`       |
| JSON data keys      | `snake_case` strings    | `"item_name"`, `"base_attack"` |

---

## State Machine Pattern

### Core Concepts

The **State Machine** is the backbone of the game's flow. Every distinct screen or mode of play is a **State**.

```
┌────────────┐   push    ┌──────────┐   push    ┌────────┐
│  MainMenu  │ ────────► │ Explore  │ ────────► │ Combat │
└────────────┘           └──────────┘           └────────┘
                           ▲  pop                  │ pop
                           └───────────────────────┘
```

### Base State Interface

Every state must implement these methods:

```python
class State:
    def enter(self, params: dict | None = None) -> None: ...
    def exit(self) -> None: ...
    def handle_events(self, events: list[pygame.event.Event]) -> None: ...
    def update(self, dt: float) -> None: ...
    def render(self, surface: pygame.Surface) -> None: ...
```

| Method          | Purpose                                                  |
|-----------------|----------------------------------------------------------|
| `enter(params)` | Called when the state becomes active. Receive setup data. |
| `exit()`        | Called when the state is removed. Clean up resources.     |
| `handle_events` | Process input events (keys, mouse, quit).                |
| `update(dt)`    | Update logic each frame (animations, timers, AI).        |
| `render(surface)` | Draw everything for this state onto the surface.       |

### StateMachine Operations

| Operation               | Behavior                                                     |
|-------------------------|--------------------------------------------------------------|
| `push(state_name, params)` | Pause current state, push new state onto the stack.       |
| `pop()`                  | Remove current state, resume the one below.                 |
| `change(state_name, params)` | Pop current state and push a new one (replace).        |

### How to Add a New State

1. Create `states/your_state.py` with a class inheriting from `State`.
2. Implement all five interface methods.
3. Register it in the state dictionary inside `Game.__init__` (in `game/game.py`).
4. Trigger a transition from another state via `self.state_machine.push("your_state")`.

---

## Code Style Rules

1. **Max line length:** 100 characters (soft limit).
2. **Docstrings:** Use them on classes and non-obvious public methods. Google style.
3. **Magic numbers:** Extract to `settings.py` constants or local named variables.
4. **Error handling:** Only at system boundaries (file I/O, asset loading). Don't wrap internal logic in try/except.
5. **Commits:** Present-tense imperative ("Add combat state", "Fix player collision").

---

## Expanding the Project — Checklist

When adding a major system, follow this pattern:

- [ ] Define its data structures (in `entities/` or `systems/`).
- [ ] Create or update relevant states (in `states/`).
- [ ] Add any new constants to `settings.py`.
- [ ] Put JSON data files in `assets/data/`.
- [ ] Register new states in `Game.__init__`.
- [ ] Update `requirements.md` milestone table.
