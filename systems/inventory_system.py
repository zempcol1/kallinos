"""Simple inventory system."""

from __future__ import annotations

import json
import os

import settings as s


def load_item_db() -> dict[str, dict]:
    """Load all items from items.json into a dict keyed by item id."""
    path = os.path.join(s.DATA_DIR, "items.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"]: item for item in data["items"]}


class Inventory:
    """Holds the player's collected items and equipped gear."""

    def __init__(self) -> None:
        self._items: list[dict] = []
        self._equipped_weapon: dict | None = None

    @property
    def items(self) -> list[dict]:
        return list(self._items)

    def add_item(self, item: dict) -> None:
        self._items.append(item)

    def remove_item(self, item_id: str) -> bool:
        for i, item in enumerate(self._items):
            if item["id"] == item_id:
                self._items.pop(i)
                if self._equipped_weapon and self._equipped_weapon["id"] == item_id:
                    self._equipped_weapon = None
                return True
        return False

    def has_item(self, item_id: str) -> bool:
        return any(item["id"] == item_id for item in self._items)

    def equip_weapon(self, item_id: str) -> bool:
        """Equip a weapon from inventory by item id."""
        for item in self._items:
            if item["id"] == item_id and item.get("type") == "weapon":
                self._equipped_weapon = item
                return True
        return False

    def get_weapon(self) -> dict | None:
        """Return the currently equipped weapon, if any."""
        return self._equipped_weapon

    def get_consumables(self) -> list[dict]:
        return [i for i in self._items if i.get("type") == "consumable"]
