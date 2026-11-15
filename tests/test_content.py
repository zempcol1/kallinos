"""The data files: they load, and everything they refer to exists.

These catch typos in JSON (an unknown item id, a map without its script...)
before they turn into a crash halfway through the game.
"""

from __future__ import annotations

import os

import pytest

import settings as s
from story import MAP_SCRIPTS
from systems import audio, content
from systems.map_system import TileMap
from systems.sprites import OBJECT_TYPES
from systems.sprites.creatures import ENEMY_GENERATORS
from systems.sprites.items import ITEM_GENERATORS

MAP_NAMES = sorted(name[:-len(".json")]
                   for name in os.listdir(os.path.join(s.DATA_DIR, "maps"))
                   if name.endswith(".json"))


def test_start_map_exists():
    assert s.START_MAP in MAP_NAMES


def test_missing_file_gives_a_clear_error():
    with pytest.raises(content.ContentError, match="nowhere.json"):
        content.load_map("nowhere")


def test_items_have_what_the_game_reads():
    for item_id, item in content.items().items():
        assert item["name"] and item["type"] in ("weapon", "consumable"), item_id
        assert item_id in ITEM_GENERATORS, f"{item_id} has no sprite"


def test_enemies_have_stats_sprites_and_known_sounds():
    effects = audio._effects()
    for enemy_id, enemy in content.enemies().items():
        assert {"name", "hp", "attack", "defense"} <= enemy.keys(), enemy_id
        assert enemy_id in ENEMY_GENERATORS, f"{enemy_id} has no sprite"
        assert enemy.get("attack_sound", "hit") in effects, enemy_id


@pytest.mark.parametrize("map_name", MAP_NAMES)
def test_map_references(map_name):
    data = content.load_map(map_name)
    tile_map = TileMap(data)

    assert data["name"] == map_name
    assert len(data["ground"]) == data["height"]
    assert all(len(row) == data["width"] for row in data["ground"])
    assert tile_map.script is None or tile_map.script in MAP_SCRIPTS
    assert tile_map.music is None or tile_map.music in audio._TRACKS

    for obj in data.get("objects", []):
        assert obj["type"] in OBJECT_TYPES, obj
        assert obj.get("harvest", "figs") in content.items(), obj
    for pickup in data.get("item_pickups", []):
        assert pickup["item_id"] in content.items(), pickup
    npc_ids = [npc["id"] for npc in data.get("npcs", [])]
    assert len(npc_ids) == len(set(npc_ids))


def test_tutorial_script_references():
    script = content.load_script("tutorial")
    tutorial = TileMap.load("tutorial")
    npc_ids = {npc["id"] for npc in tutorial.npc_data}

    assert script["enemy"] in content.enemies()
    assert script["required_item"] in content.items()
    assert tutorial.get_trigger(script["trigger"]) is not None
    assert script["missing_npc"] in npc_ids
    assert tutorial.get_prop(script["shimmer_object"]) is not None
    assert script["title_card"]["next_map"] in MAP_NAMES
    for key in ("intro", "missing_item", "reveal", "victory"):
        assert all(len(line) == 2 for line in script[key]), key
