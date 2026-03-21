from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    override = os.environ.get("WAWA_KANBAN_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def openclaw_state_dir() -> Path:
    raw = os.environ.get("OPENCLAW_STATE_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".openclaw"


def openclaw_config_path() -> Path:
    raw = os.environ.get("OPENCLAW_CONFIG_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return openclaw_state_dir() / "openclaw.json"


def to_config_path(p: Path) -> str:
    """Prefer ~/.-relative strings when under HOME (OpenClaw docs style)."""
    p = p.expanduser().resolve()
    home = Path.home().resolve()
    try:
        rel = p.relative_to(home)
        return str(Path("~") / rel).replace("\\", "/")
    except ValueError:
        return str(p)
