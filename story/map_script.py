"""Base class for map-specific story scripts run inside Exploration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from states.exploration import Exploration


class MapScript:
    """Story hooks for one map. The base class is plain free roam.

    Exploration owns the map, player and NPCs and calls these hooks; scripts
    drive the story through Exploration's public helpers (``show_toast``,
    ``push_dialogue``, ``start_combat``, ``fade_out``, ``get_npc``...).
    """

    def __init__(self, scene: Exploration) -> None:
        self.scene = scene

    def on_start(self) -> None:
        """Called once the map has faded in."""

    def allows_control(self) -> bool:
        """Whether the player may move and interact right now."""
        return True

    def update(self, dt: float) -> None:
        """Per-frame logic (trigger checks, timers)."""

    def on_dialogue_complete(self, event_id: str) -> None:
        """A dialogue pushed with ``on_complete=event_id`` has finished."""

    def on_combat_victory(self) -> None:
        """A fight started by this script was won."""

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Draw script effects above the world, below the HUD."""
