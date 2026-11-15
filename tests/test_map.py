"""TileMap: collisions, triggers, props and the camera, on a tiny hand-made map."""

from __future__ import annotations

import pygame

import settings as s
from systems.camera import Camera
from systems.map_system import TILE_GRASS, TILE_PATH, TileMap

T = s.SCALED_TILE


def make_map(**extra) -> TileMap:
    data = {
        "name": "test", "width": 6, "height": 5, "player_start": [1, 1],
        "ground": [[0] * 6, [0, 1, 1, 0, 0, 0], [0] * 6, [0] * 6, [0] * 6],
        **extra,
    }
    return TileMap(data)


def test_size_tiles_and_defaults():
    tile_map = make_map()
    assert (tile_map.pixel_width, tile_map.pixel_height) == (6 * T, 5 * T)
    assert tile_map.display_name == "test"
    assert tile_map.tile_at(T * 1.5, T * 1.5) == TILE_PATH
    assert tile_map.tile_at(5, 5) == TILE_GRASS
    assert tile_map.tile_at(-5, 5) is None


def test_map_edges_are_walls():
    tile_map = make_map()
    inside = pygame.Rect(T, T, T, T)
    assert inside.collidelist(tile_map.collisions) == -1
    width, height = tile_map.pixel_width, tile_map.pixel_height
    for edge in ((-1, T), (width, T), (T, -1), (T, height)):     # one pixel outside
        assert pygame.Rect(edge, (1, 1)).collidelist(tile_map.collisions) != -1


def test_collisions_and_triggers_are_in_pixels():
    tile_map = make_map(collisions=[{"x": 2, "y": 2, "w": 1.5, "h": 1}],
                        triggers=[{"id": "zone", "x": 0.5, "y": 3, "w": 2, "h": 1}])
    assert pygame.Rect(2 * T, 2 * T, T * 3 // 2, T) in tile_map.collisions
    assert tile_map.get_trigger("zone") == pygame.Rect(T // 2, 3 * T, 2 * T, T)
    assert tile_map.get_trigger("elsewhere") is None


def test_sorted_objects_become_props_with_footprints():
    tile_map = make_map(objects=[
        {"type": "boulder", "id": "rock", "x": 1, "y": 2, "w": 2, "h": 2},
        {"type": "bush", "x": 4, "y": 0, "w": 1, "h": 1, "solid": False},
    ])
    rock = tile_map.get_prop("rock")
    assert rock is not None and rock.footprints
    assert all(footprint in tile_map.collisions for footprint in rock.footprints)
    assert rock.depth == max(footprint.bottom for footprint in rock.footprints)

    bush = next(prop for prop in tile_map.props if prop.type == "bush")
    assert all(footprint not in tile_map.collisions for footprint in bush.footprints)


def test_fence_runs_split_into_linked_tiles():
    tile_map = make_map(objects=[{"type": "fence", "x": 1, "y": 3, "w": 3, "h": 1},
                                 {"type": "fence", "x": 1, "y": 3, "w": 1, "h": 2}])
    fences = [prop for prop in tile_map.props if prop.type == "fence"]
    assert len(fences) == 4     # 3 + 2 tiles, the shared corner only once


def test_fig_tree_is_harvested_once():
    tile_map = make_map(objects=[{"type": "fig_tree", "x": 1, "y": 1, "w": 3, "h": 3,
                                  "harvest": "figs"}])
    tree = tile_map.props[0]
    ripe = tree.sprite
    assert tree.can_harvest
    assert tree.pick() == "figs"
    assert not tree.can_harvest and tree.pick() is None
    assert tree.sprite is not ripe


def test_camera_follows_and_clamps():
    camera = Camera(s.SCREEN_WIDTH * 2, s.SCREEN_HEIGHT * 2)
    camera.follow(0, 0)
    assert (camera.x, camera.y) == (0, 0)
    camera.follow(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
    assert (camera.x, camera.y) == (s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT // 2)
    camera.follow(10 ** 6, 10 ** 6)
    assert (camera.x, camera.y) == (s.SCREEN_WIDTH, s.SCREEN_HEIGHT)


def test_camera_centers_small_maps():
    camera = Camera(s.SCREEN_WIDTH - 100, s.SCREEN_HEIGHT - 60)
    camera.follow(0, 0)
    assert (camera.x, camera.y) == (-50, -30)
