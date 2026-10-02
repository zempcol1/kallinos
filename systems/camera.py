"""Camera that follows the player and clamps to map bounds."""

from __future__ import annotations

import settings as s


class Camera:
    """Simple camera offset that centers on a target position.

    Maps smaller than the screen are centered instead of pinned top-left.
    """

    def __init__(self, map_pixel_w: int, map_pixel_h: int) -> None:
        self.x = 0
        self.y = 0
        self._map_w = map_pixel_w
        self._map_h = map_pixel_h

    def follow(self, target_x: float, target_y: float) -> None:
        """Center the camera on the target, clamped to map edges."""
        self.x = self._axis(target_x, s.SCREEN_WIDTH, self._map_w)
        self.y = self._axis(target_y, s.SCREEN_HEIGHT, self._map_h)

    @staticmethod
    def _axis(target: float, screen: int, world: int) -> int:
        if world <= screen:
            return -(screen - world) // 2
        return max(0, min(int(target - screen // 2), world - screen))
