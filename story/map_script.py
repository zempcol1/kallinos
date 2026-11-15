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
    ``give_item``, ``push_dialogue``, ``start_combat``, ``fade_out``,
    ``get_npc``...). Dialogue and combat take a callback for what comes next,
    so a beat reads ``push_dialogue(lines, self._next_beat)``.
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

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Draw script effects above the world, below the HUD."""
