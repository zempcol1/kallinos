"""What the exploration state needs from anything the player can use with E."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from entities.player import Player
    from states.exploration import Exploration


class Interactable(Protocol):
    """A pickup, a harvestable prop, a person... later signs, chests and doors.

    Exploration shows the prompt bubble over the first interactable in reach
    and calls ``interact`` when the player presses the interact key.
    """

    def in_reach(self, player: Player) -> bool:
        """Whether the player could use this right now."""

    @property
    def prompt_anchor(self) -> tuple[int, int]:
        """World position the prompt bubble's tip points at."""

    def interact(self, scene: Exploration) -> None:
        """Do it: act through the scene's helpers (toasts, items, dialogue)."""
