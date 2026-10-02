"""GameSession — everything that persists across maps for one playthrough."""

from __future__ import annotations

import copy

from entities.player import Player


class GameSession:
    """Owns the player for a whole playthrough, plus a retry checkpoint.

    Until save/load exists, the checkpoint is taken whenever a map is
    entered: retrying after a defeat restarts that map with the player as
    they were on arrival.
    """

    def __init__(self, start_map: str) -> None:
        self.player = Player(0, 0)
        self.current_map = start_map
        self._checkpoint_map = start_map
        self._checkpoint_player = copy.deepcopy(self.player)

    def checkpoint(self, map_name: str) -> None:
        """Remember the current map and a snapshot of the player."""
        self.current_map = map_name
        self._checkpoint_map = map_name
        self._checkpoint_player = copy.deepcopy(self.player)

    def restore_checkpoint(self) -> str:
        """Roll the player back to the last checkpoint; returns its map name."""
        self.player = copy.deepcopy(self._checkpoint_player)
        self.current_map = self._checkpoint_map
        return self._checkpoint_map
