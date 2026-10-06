# Kallinos — Rise of a Mortal

A 2D turn-based RPG set in Ancient Greece. Start as a nobody from the village
of Kyrillos, armed with a stick, and rise to legend and beyond.
Built with Python and pygame-ce; all art is currently generated in code.

## Quick start

Requires Python 3.12+.

```bash
pip install pygame-ce
python main.py
```

## Windows executable

To get a single `Kallinos.exe` that runs on any Windows PC without Python:

```bash
pip install pygame-ce pyinstaller
python build_exe.py
```

The game is written to `dist/Kallinos.exe`; copy it anywhere and double-click.
Rebuild after changing the game.

## Controls

| Key           | Action                       |
|---------------|------------------------------|
| WASD / Arrows | Move, navigate menus         |
| E / Enter     | Interact, advance dialogue   |
| Enter / Space | Confirm                      |
| ESC           | Back to main menu            |

## What's playable

- **Tutorial:** the garden, Niko's disappearance, figs picked from the fig
  trees, the olive-wood branch, and a turn-based fight with the Vátrachos (a
  very large frog).
- **Kyrillos village:** free roam and talking to villagers.

Next up: persistent progress across maps, data-driven cutscenes and quests,
deeper combat, and the rest of Act I.

## Docs

- [design.md](design.md): story, gameplay, art and audio direction
- [CLAUDE.md](CLAUDE.md): architecture, data formats, conventions
