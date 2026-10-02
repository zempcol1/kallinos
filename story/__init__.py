"""Map story scripts. A map opts in with ``"script": "<id>"`` in its JSON."""

from story.map_script import MapScript
from story.tutorial import TutorialScript

MAP_SCRIPTS: dict[str, type[MapScript]] = {
    "tutorial": TutorialScript,
}

__all__ = ["MAP_SCRIPTS", "MapScript", "TutorialScript"]
