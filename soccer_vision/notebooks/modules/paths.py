from __future__ import annotations
from pathlib import Path
import os

ROOT_NAME = "soccer_vision"

def find_repo_root(root_name: str = ROOT_NAME) -> Path:
    """
    Find the 'soccer_vision' folder no matter where this notebook runs:
    - honors SOCCER_VISION_ROOT if set and valid
    - if CWD is soccer_vision/ or soccer_vision/notebooks/, use that
    - if CWD is footbot/ (parent), use footbot/soccer_vision if it exists
    - otherwise walk upwards to find a folder literally named 'soccer_vision'
    """
    env = os.getenv("SOCCER_VISION_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if (p.name == root_name) and (p / "notebooks").exists():
            return p

    here = Path.cwd().resolve()

    # Already at repo root?
    if here.name == root_name and (here / "notebooks").exists():
        return here

    # Inside the notebooks folder of the repo?
    if here.name == "notebooks" and here.parent.name == root_name:
        return here.parent

    # Running from parent (e.g., footbot/)? Use direct child if present.
    direct = here / root_name
    if direct.exists() and (direct / "notebooks").exists():
        return direct

    # Walk upwards for a folder literally named 'soccer_vision'
    for p in [here, *here.parents]:
        if p.name == root_name and (p / "notebooks").exists():
            return p

    raise FileNotFoundError(
        f"Could not locate '{root_name}' from {here}. "
        f"Optionally set SOCCER_VISION_ROOT to the absolute path."
    )

def base_paths(repo_root: Path | None = None):
    base = (repo_root or find_repo_root()).resolve()
    return {
        "BASE": base,
        "DATASET": base / "dataset",
        "MODELS":  base / "models",
        "RUNS":    base / "runs",
        "DATA_YAML": base / "data.yaml",
    }