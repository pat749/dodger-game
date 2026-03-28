"""Legacy entry: runs the game from the repository `game/` folder."""
from __future__ import annotations

import pathlib
import runpy

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
runpy.run_path(str(_REPO_ROOT / "game" / "main.py"), run_name="__main__")
