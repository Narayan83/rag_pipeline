"""Load config.yaml from the project root."""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache

import yaml

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_config() -> dict:
    path = ROOT / "config.yaml"
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def project_path(key: str) -> Path:
    cfg = load_config()
    return (ROOT / cfg["paths"][key]).resolve()
