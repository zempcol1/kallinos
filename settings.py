"""Global constants and configuration for Kallinos."""

import os

# ── Display ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GAME_TITLE = "Kallinos — Rise of a Mortal"

# ── Tile / Map ───────────────────────────────────────────────────────────────
TILE_SIZE = 16          # Logical tile size in pixels
SCALE = 3               # Render scale (16 × 3 = 48px on screen)
SCALED_TILE = TILE_SIZE * SCALE   # 48
PLAYER_SPEED = 120      # Pixels per second (at scale)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
MAPS_DIR = os.path.join(DATA_DIR, "maps")

# ── Colors (from visual_styling.md palettes) ────────────────────────────────
# Menu / UI
COLOR_MENU_BG = (15, 15, 35)         # #0F0F23
COLOR_TITLE_GOLD = (241, 196, 15)    # #F1C40F
COLOR_ACCENT_GOLD = (212, 168, 68)   # #D4A844
COLOR_BUTTON_NORMAL = (44, 62, 80)   # #2C3E50
COLOR_BUTTON_HOVER = (52, 73, 94)    # #34495E
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_DIM = (149, 165, 166)      # #95A5A6
COLOR_BLACK = (0, 0, 0)

# Combat
COLOR_COMBAT_BG = (26, 26, 46)       # #1A1A2E
COLOR_PANEL_BLUE = (22, 33, 62)      # #16213E
COLOR_HP_RED = (192, 57, 43)         # #C0392B
COLOR_MP_BLUE = (41, 128, 185)       # #2980B9
COLOR_XP_GREEN = (39, 174, 96)       # #27AE60
COLOR_TEXT_LIGHT = (236, 240, 241)    # #ECF0F1

# Exploration
COLOR_OLIVE_GREEN = (107, 142, 78)   # #6B8E4E
COLOR_SAND = (232, 213, 163)         # #E8D5A3
COLOR_DEEP_SEA = (27, 79, 114)       # #1B4F72

# Tile palette (for procedural map rendering)
TILE_COLORS = {
    0: (107, 142, 78),    # grass
    1: (193, 178, 140),   # dirt path
    2: (160, 140, 110),   # stone wall
    3: (180, 120, 90),    # house wall
    4: (170, 90, 60),     # house roof / door
    5: (80, 110, 55),     # dark green (tree canopy)
    6: (120, 120, 110),   # boulder
    7: (90, 70, 50),      # tree trunk
    8: (200, 185, 155),   # fence
    9: (75, 100, 50),     # bush
}

# Dialogue box
COLOR_DIALOGUE_BG = (15, 15, 35, 230)
COLOR_DIALOGUE_BORDER = (212, 168, 68)

# Toast
COLOR_TOAST_BG = (30, 30, 50, 200)
