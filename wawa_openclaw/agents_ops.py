from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from wawa_openclaw.paths import openclaw_state_dir, repo_root, to_config_path

ALLOWED_ROLES = frozenset(
    {
        "designer",
        "developer",
        "code-verifier",
        "general-verifier",
        "lead",
        "project-manager",
    }
)

_SLUG = re.compile(r"[^a-z0-9-]+")


def slugify_agent_id(name: str) -> str:
    s = name.strip().lower().replace("_", "-")
    s = _SLUG.sub("-", s).strip("-")
    if not s:
        raise ValueError("Name must yield a non-empty agent id (use letters, digits, or hyphen).")
    return s


def _copy_role_templates(role_src: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for item in role_src.iterdir():
        if item.name.startswith("."):
            continue
        dest = workspace / item.name
        if item.is_file():
            shutil.copy2(item, dest)
        elif item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)


def plan_add_agent(
    *,
    name: str,
    role: str,
    root: Path | None = None,
    state: Path | None = None,
) -> tuple[dict[str, Any], Path, Path, Path]:
    """Validate paths and build config entry; does not create files on disk."""
    if role not in ALLOWED_ROLES:
        raise ValueError(
            f"Unknown role {role!r}. Expected one of: {', '.join(sorted(ALLOWED_ROLES))}"
        )
    root = root or repo_root()
    state = state or openclaw_state_dir()
    role_src = root / "agents" / role
    if not role_src.is_dir():
        raise ValueError(f"Role template directory missing: {role_src}")

    agent_id = slugify_agent_id(name)
    workspace = state / f"workspace-wawa-{agent_id}"
    agent_dir = state / "agents" / agent_id / "agent"
    agent_root = state / "agents" / agent_id

    if agent_root.exists():
        raise ValueError(
            f"OpenClaw agent state already exists: {agent_root}. "
            "Remove the agent first or pick another name."
        )
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError(
            f"Workspace already exists and is not empty: {workspace}. "
            "Remove the agent first or pick another name."
        )

    entry: dict[str, Any] = {
        "id": agent_id,
        "name": name.strip(),
        "workspace": to_config_path(workspace),
        "agentDir": to_config_path(agent_dir),
    }
    return entry, workspace, agent_dir, role_src


def materialize_agent(*, workspace: Path, agent_dir: Path, role_src: Path) -> None:
    """Create agentDir and copy role templates into workspace (after config is saved)."""
    agent_dir.parent.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)
    _copy_role_templates(role_src, workspace)


def merge_agent_into_config(cfg: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    lst = cfg["agents"]["list"]
    if any(isinstance(a, dict) and a.get("id") == entry["id"] for a in lst):
        raise ValueError(f"Agent id already in openclaw.json: {entry['id']}")
    lst.append(entry)
    return cfg


def remove_agent_from_config(cfg: dict[str, Any], agent_id: str) -> dict[str, Any]:
    lst = cfg["agents"]["list"]
    new_list = [a for a in lst if not (isinstance(a, dict) and a.get("id") == agent_id)]
    if len(new_list) == len(lst):
        raise ValueError(f"No agent with id {agent_id!r} in agents.list")
    cfg["agents"]["list"] = new_list

    bindings = cfg.get("bindings")
    if isinstance(bindings, list):
        cfg["bindings"] = [b for b in bindings if not (isinstance(b, dict) and b.get("agentId") == agent_id)]
    return cfg


def purge_agent_paths(agent_id: str, state: Path | None = None) -> None:
    state = state or openclaw_state_dir()
    workspace = state / f"workspace-wawa-{agent_id}"
    agent_tree = state / "agents" / agent_id
    if workspace.is_dir():
        shutil.rmtree(workspace)
    if agent_tree.is_dir():
        shutil.rmtree(agent_tree)
