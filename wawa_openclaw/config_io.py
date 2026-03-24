from __future__ import annotations

import json5
import shutil
from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    data = json5.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object at root in {path}, got {type(data).__name__}")
    return data


def save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        backup = path.parent / f"{path.name}.bak.wawa"
        shutil.copy2(path, backup)
    out = json5.dumps(data, indent=2, quote_keys=True, trailing_commas=False)
    path.write_text(out + "\n", encoding="utf-8")


def ensure_agents_tree(cfg: dict[str, Any]) -> dict[str, Any]:
    if "agents" not in cfg or not isinstance(cfg["agents"], dict):
        cfg["agents"] = {}
    agents = cfg["agents"]
    if "defaults" not in agents or not isinstance(agents["defaults"], dict):
        agents["defaults"] = {}
    if "list" not in agents or agents["list"] is None:
        agents["list"] = []
    if not isinstance(agents["list"], list):
        raise ValueError("agents.list must be a list")
    return cfg
