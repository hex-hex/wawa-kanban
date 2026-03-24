"""Resolve Wawa workspace root (contains ``projects/`` and ``agents/``)."""

from __future__ import annotations

import os
from pathlib import Path


def workspace_base(*, override: Path | None = None) -> Path:
    """Workspace root directory.

    Resolution: ``override`` if set, else ``WAWA_WORKSPACE_PATH``, else
    ``~/.wawa-kanban/workspace`` (same default as the ``wkanban`` bootstrap script).
    """
    if override is not None:
        return override.expanduser().resolve()
    raw = os.environ.get("WAWA_WORKSPACE_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".wawa-kanban" / "workspace").resolve()


def projects_dir(workspace_root: Path) -> Path:
    return workspace_root / "projects"


# Same agent ticket slots as ``cli/wkanban`` ``ensure_dirs`` / ``install.sh`` (under workspace ``agents/``).
_INIT_AGENT_SLOT_PARTS: tuple[tuple[str, str], ...] = (
    ("designers", "default"),
    ("developers", "default"),
    ("info-officers", "default"),
    ("code-verifiers", "default"),
    ("general-verifiers", "default"),
)


def ensure_init_agent_slot_dirs(workspace_root: Path) -> None:
    """Create empty kanban agent directories (``mkdir -p`` semantics)."""
    base = workspace_root / "agents"
    for type_folder, name in _INIT_AGENT_SLOT_PARTS:
        (base / type_folder / name).mkdir(parents=True, exist_ok=True)
