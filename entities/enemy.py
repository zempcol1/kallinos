"""Enemy entity for combat."""

from __future__ import annotations


class Enemy:
    """An enemy combatant, built from one entry of enemies.json.

    Besides the stats, an entry can carry the enemy's own flavour:
    ``attack_text``, ``defeat_text`` and ``attack_sound`` (an effect name).
    """

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.description: str = data.get("description", "")
        self.max_hp: int = data["hp"]
        self.hp: int = data["hp"]
        self.attack: int = data["attack"]
        self.defense: int = data["defense"]
        self.xp_reward: int = data.get("xp_reward", 0)
        self.attack_text: str = data.get("attack_text", f"{self.name} attacks!")
        self.defeat_text: str = data.get("defeat_text", f"{self.name} is defeated!")
        self.attack_sound: str | None = data.get("attack_sound")
