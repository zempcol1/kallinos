"""Sprite smoke tests: every generator draws something without raising."""

from __future__ import annotations

import pygame
import pytest

import settings as s
from systems.sprites import (
    DIRECTIONS, OBJECT_TYPES, PLAYER_LOOK, PORTRAIT_SIZE, WALK_FRAMES, Look, app_icon,
    battle_pose, character, character_shadow, combat_backdrop, continue_arrow, dirt_path,
    earth, enemy, grass, interact_bubble, item, laurel, portrait, title,
)
from systems.sprites.characters import HAIR_STYLES
from systems.sprites.creatures import ENEMY_GENERATORS, ENEMY_IDLE_FRAMES
from systems.sprites.items import ITEM_GENERATORS
from systems.sprites.pixel_art import from_grid
from systems.sprites.portraits import PORTRAIT_SCALE
from ui.pixel_font import _GLYPHS
from ui.widgets import font, wrap_text

FACES = ("plain", "cheeky", "bold", "worried", "wise")
# One sensible size per object type, as used in the maps
OBJECT_SIZES = {"house": (7, 4), "temple": (7, 6), "stone_wall": (8, 3), "well": (2, 2),
                "amphorae": (1, 1), "olive_tree": (3, 3), "cypress": (2, 4),
                "plane_tree": (6, 6), "aleppo_pine": (4, 5), "fig_tree": (3, 3),
                "bush": (1, 1), "boulder": (2, 2)}


def has_pixels(surface: pygame.Surface) -> bool:
    """Anything drawn at all, translucent shadows included."""
    return surface.get_bounding_rect(min_alpha=1).width > 0


@pytest.mark.parametrize("type_name", sorted(OBJECT_TYPES))
def test_object_types_draw(type_name):
    kind = OBJECT_TYPES[type_name]
    geometry = ((True, False, True, False),) if kind.tiled else OBJECT_SIZES[type_name]
    for variant in range(3):
        assert has_pixels(kind.draw(*geometry, variant))
    if kind.footprint:
        assert kind.footprint(*geometry)
    if kind.shadow:
        assert kind.shadow(*geometry, 0)
    if kind.harvestable:
        assert has_pixels(kind.draw(*geometry, 0, ripe=False))


def test_every_object_type_has_a_test_size():
    assert {name for name, kind in OBJECT_TYPES.items() if not kind.tiled} == set(OBJECT_SIZES)


@pytest.mark.parametrize("hair_style", HAIR_STYLES)
def test_characters_walk_in_all_directions(hair_style):
    look = Look(tunic=(200, 120, 80), hair_style=hair_style, bearded=True)
    sizes = {character(look, direction, frame).get_size()
             for direction in DIRECTIONS for frame in range(WALK_FRAMES)}
    assert len(sizes) == 1      # every frame the same size: no jitter while walking


def test_player_look_everywhere_it_is_drawn():
    assert has_pixels(character(PLAYER_LOOK, "down_left", 1))
    assert has_pixels(battle_pose(PLAYER_LOOK, "ready"))
    assert has_pixels(battle_pose(PLAYER_LOOK, "strike"))
    assert has_pixels(character_shadow())
    assert app_icon(s.ICON_SIZE).get_size() == (s.ICON_SIZE, s.ICON_SIZE)


@pytest.mark.parametrize("face", FACES)
def test_portraits(face):
    look = Look(tunic=(80, 130, 200), face=face, hair_style="elder", bearded=True)
    for talking in (False, True):
        for blinking in (False, True):
            bust = portrait(look, talking, blinking)
            assert bust.get_size() == (PORTRAIT_SIZE * PORTRAIT_SCALE,) * 2


def test_enemies_and_items():
    for enemy_id in ENEMY_GENERATORS:
        for frame in range(ENEMY_IDLE_FRAMES[enemy_id]):
            assert has_pixels(enemy(enemy_id, frame, s.COMBAT_SCALE))
    assert has_pixels(enemy("not_drawn_yet"))           # placeholder blob
    for item_id in ITEM_GENERATORS:
        assert has_pixels(item(item_id))
    assert item("not_drawn_yet") is None                # callers fall back to a color


def test_tiles_icons_and_scenes():
    edges = (True, False, True, False)
    for surface in (grass(0), grass(3), grass(4), dirt_path(edges), earth(edges, 1),
                    interact_bubble(), continue_arrow(), laurel(), laurel(flip=True),
                    title.sky(), title.sea(), title.islands(), title.headland(),
                    title.foreground(), title.logo(), title.gull(0), title.cloud(40, 1)):
        assert has_pixels(surface)
    backdrop = combat_backdrop((190, 410), (566, 252))
    assert backdrop.get_size() == (s.SCREEN_WIDTH, s.SCREEN_HEIGHT)


def test_ragged_grids_are_rejected():
    with pytest.raises(ValueError):
        from_grid(["ab", "a"], {"a": (0, 0, 0), "b": (9, 9, 9)})


def test_pixel_font_draws_every_glyph():
    small = font(20)
    for ch in _GLYPHS:
        assert small.render(ch).get_height() == small.get_height()
    assert small.size("") == (0, small.get_height())
    assert small.render("ж").get_size() == small.render("?").get_size()   # unknown → "?"
    assert font(30).scale > small.scale


def test_wrap_text_fits_the_width():
    text = "A fat, hissing frog the size of a cat stares back at you."
    wrapped = wrap_text(text, font(30), 300)
    assert len(wrapped) > 1
    assert " ".join(wrapped) == text
    assert all(font(30).size(line)[0] <= 300 for line in wrapped)
