"""The player's inventory."""

from __future__ import annotations

from systems import content


class Inventory:
    """What the player carries: item ids with counts, plus the equipped weapon.

    Only ids are stored (which keeps it trivial to save); the item data comes
    from ``content.items()``. Items keep the order they were first picked up in.
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._weapon_id: str | None = None

    def add_item(self, item_id: str, count: int = 1) -> None:
        if item_id not in content.items():
            raise KeyError(f"Unknown item id {item_id!r}")
        self._counts[item_id] = self._counts.get(item_id, 0) + count

    def remove_item(self, item_id: str) -> bool:
        """Take one away; False if there was none. The last weapon is unequipped."""
        if item_id not in self._counts:
            return False
        self._counts[item_id] -= 1
        if self._counts[item_id] <= 0:
            del self._counts[item_id]
            if self._weapon_id == item_id:
                self._weapon_id = None
        return True

    def has_item(self, item_id: str) -> bool:
        return item_id in self._counts

    def count(self, item_id: str) -> int:
        return self._counts.get(item_id, 0)

    def equip_weapon(self, item_id: str) -> bool:
        """Equip a carried weapon by id; False if it isn't carried or isn't a weapon."""
        if not self.has_item(item_id) or content.items()[item_id].get("type") != "weapon":
            return False
        self._weapon_id = item_id
        return True

    @property
    def weapon(self) -> dict | None:
        """The equipped weapon's item data, if any."""
        return content.items()[self._weapon_id] if self._weapon_id else None

    def stacks(self, item_type: str | None = None) -> list[tuple[dict, int]]:
        """Carried items as (item data, count), optionally only one ``type``."""
        items = content.items()
        return [(items[item_id], count) for item_id, count in self._counts.items()
                if item_type is None or items[item_id].get("type") == item_type]
