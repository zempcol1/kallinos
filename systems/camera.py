"""Camera that follows the player and clamps to map bounds."""

from __future__ import annotations

import settings as s


class Camera:
    """Simple camera offset that centers on a target position."""

    def __init__(self, map_pixel_w: int, map_pixel_h: int) -> None:
        self.x = 0
        self.y = 0
        self._map_w = map_pixel_w
        self._map_h = map_pixel_h

    def follow(self, target_x: float, target_y: float) -> None:
        """Center the camera on the target, clamped to map edges."""
        self.x = int(target_x - s.SCREEN_WIDTH // 2)
        self.y = int(target_y - s.SCREEN_HEIGHT // 2)

        # Clamp
        self.x = max(0, min(self.x, self._map_w - s.SCREEN_WIDTH))
        self.y = max(0, min(self.y, self._map_h - s.SCREEN_HEIGHT))
