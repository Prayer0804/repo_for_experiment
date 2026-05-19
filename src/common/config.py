from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path = "config/config.yaml") -> dict[str, Any]:
    config_path = ROOT / path
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def project_path(path: str | Path) -> Path:
    return ROOT / Path(path)


def ensure_dirs(config: dict[str, Any]) -> None:
    for value in config["paths"].values():
        project_path(value).mkdir(parents=True, exist_ok=True)


def configured_path(config: dict[str, Any], section: str, key: str) -> Path:
    return project_path(config[section][key])
