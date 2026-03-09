# Kallinos — Visual Styling Guide

## Art Direction

### Overall Aesthetic
- **Style:** 16-bit pixel art, inspired by SNES-era RPGs and the Harry Potter GBC/GBA games.
- **Tile size:** 16×16 pixels (scalable to 32×32 or 48×48 on screen via integer scaling).
- **Character sprites:** 16×24 or 16×32 base size, with 4-directional walk cycles (3–4 frames each).
- **Perspective:** Top-down with slight 3/4 view for exploration. Side-view for combat.

### Ancient Greece Theme
The pixel art should evoke the Mediterranean world without strict historical accuracy:
- White/cream stone buildings with terracotta roofs.
- Olive trees, grapevines, cypress trees, marble columns.
- Coastal areas with deep blue sea, sandy shores.
- Interiors: wooden furniture, amphorae, hanging fabrics, oil lamps.
- Temples with painted columns (Greeks painted their marble — use subtle color accents).
- Underworld areas: dark stone, green/blue ghostly light, river Styx motifs.
- Olympus areas: brilliant white, gold, clouds, ethereal glow.

---

## Color Palettes

### Exploration — Mediterranean Coast
| Role        | Hex       | Use                              |
|-------------|-----------|----------------------------------|
| Sand        | `#E8D5A3` | Beaches, paths                   |
| Olive Green | `#6B8E4E` | Trees, grass                     |
| Deep Sea    | `#1B4F72` | Ocean, deep water                |
| Sky Blue    | `#85C1E9` | Shallow water, sky               |
| Terracotta  | `#C0725E` | Rooftops, pottery                |
| Marble      | `#F2EFEA` | Columns, temples, statues        |
| Stone       | `#8D8D8D` | Walls, floors                    |
| Dark Wood   | `#5D4037` | Doors, furniture                 |

### Combat Screen
| Role             | Hex       | Use                              |
|------------------|-----------|----------------------------------|
| Background Dark  | `#1A1A2E` | Combat backdrop base             |
| Panel Blue       | `#16213E` | UI panels, menu background       |
| Accent Gold      | `#D4A844` | Selected option, highlights      |
| Health Red       | `#C0392B` | HP bar fill                      |
| Mana Blue        | `#2980B9` | MP bar fill                      |
| XP Green         | `#27AE60` | XP bar fill                      |
| Text Light       | `#ECF0F1` | Primary text                     |
| Text Dim         | `#95A5A6` | Secondary/disabled text          |

### Menu / UI
| Role             | Hex       | Use                              |
|------------------|-----------|----------------------------------|
| Menu BG          | `#0F0F23` | Main menu background             |
| Title Gold       | `#F1C40F` | Game title, headings             |
| Button Normal    | `#2C3E50` | Unselected menu buttons          |
| Button Hover     | `#34495E` | Hovered/selected buttons         |
| Border           | `#D4A844` | Panel borders, dividers          |
| White            | `#FFFFFF` | Clean text on dark backgrounds   |

---

## UI Layout

### Main Menu
```
┌──────────────────────────────────────┐
│                                      │
│           K A L L I N O S            │  ← Title in large pixel font, gold
│        ~ Rise of a Mortal ~          │  ← Subtitle, smaller, off-white
│                                      │
│          ▸ New Game                  │  ← Selected (gold highlight)
│            Continue                  │
│            Settings                  │
│            Quit                      │
│                                      │
│                                      │
│   v0.1              © 2026           │  ← Footer, dim text
└──────────────────────────────────────┘
```

### Exploration HUD (future)
```
┌──────────────────────────────────────┐
│ [Portrait] HP ████████░░  120/150    │  ← Top bar, semi-transparent
│            MP ██████░░░░   45/80     │
├──────────────────────────────────────┤
│                                      │
│          (tile-based world)          │
│                                      │
│                                      │
│                                      │
├──────────────────────────────────────┤
│  Location: Village of Kyrillos       │  ← Bottom info bar
│  Quest: Speak to the Elder           │
└──────────────────────────────────────┘
```

### Turn-Based Combat (Harry Potter GBC/GBA Style)
```
┌──────────────────────────────────────┐
│                                      │
│        [Enemy Sprite]                │  ← Center-right, larger sprite
│        HP ██████░░░░                 │
│                                      │
│──────────────────────────────────────│
│ [Player Sprite]                      │  ← Lower-left, facing right
│                                      │
│ ┌──────────────────────────────────┐ │
│ │  ▸ Attack      Defend           │ │  ← Action menu panel
│ │    Skill       Item             │ │
│ │    Flee                         │ │
│ └──────────────────────────────────┘ │
│  HP ████████░░  120/150   MP 45/80   │  ← Player stats bar
└──────────────────────────────────────┘
```

**Combat flow visuals:**
- When an action is selected, the acting sprite briefly animates (lunge, flash, shake).
- Damage numbers pop up over the target and float upward before fading.
- HP bars animate smoothly when taking damage (not instant).
- Screen flashes white on critical hits.
- Defeated enemies fade out; victory fanfare plays.

---

## Typography

| Context          | Font Style                  | Size (at 1x) |
|------------------|-----------------------------|---------------|
| Game title       | Large pixel/serif font      | 48px          |
| Menu options     | Clean pixel font            | 24px          |
| Dialogue text    | Clean pixel font            | 16px          |
| Damage numbers   | Bold pixel font             | 20px          |
| HUD labels       | Small pixel font            | 12px          |

**Recommended free pixel fonts:**
- Press Start 2P (Google Fonts)
- Pixel Operator
- Silver (Poppy Works)

Until custom fonts are added, the system will use Pygame's built-in default font at appropriate sizes.

---

## Animation Guidelines

| Animation          | Frames | Speed         | Notes                           |
|--------------------|--------|---------------|---------------------------------|
| Walk cycle         | 4      | 150ms/frame   | Per direction (up/down/left/right) |
| Idle               | 2      | 500ms/frame   | Subtle breathing motion         |
| Attack (combat)    | 3–4    | 80ms/frame    | Quick lunge + return            |
| Hit reaction       | 2      | 100ms/frame   | Flash white + knockback         |
| Death              | 4      | 120ms/frame   | Collapse or fade                |
| Menu cursor        | 2      | 300ms/frame   | Pulsing or bouncing arrow       |
| Screen transition  | —      | 300–500ms     | Fade to black, then fade in     |

---

## Visual Feedback Principles

1. **Every input should have visible feedback.** Menu selection changes color; attacks show impact.
2. **Emphasize state changes.** Entering combat triggers a transition effect. Leveling up flashes the screen.
3. **Readability first.** High contrast between text and background. UI panels have solid or semi-transparent dark backgrounds behind text.
4. **Consistent visual language.** Gold = important/selected. Red = damage/danger. Green = healing/positive. Blue = mana/information.
