"""Enemy entity for combat."""

from __future__ import annotations

import json
import os

import settings as s


def load_enemy_db() -> dict[str, dict]:
    """Load all enemies from enemies.json into a dict keyed by id."""
    path = os.path.join(s.DATA_DIR, "enemies.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["id"]: e for e in data["enemies"]}


class Enemy:
    """An enemy combatant, instantiated from data."""

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.description: str = data.get("description", "")
        self.max_hp: int = data["hp"]
        self.hp: int = data["hp"]
        self.attack: int = data["attack"]
        self.defense: int = data["defense"]
        self.xp_reward: int = data.get("xp_reward", 0)
