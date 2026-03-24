"""OpenClaw agent subcommands for the wkanban CLI (e.g. list, add-default)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from wawa_cli.workspace_paths import ensure_init_agent_slot_dirs, workspace_base
from wawa_openclaw.agents_ops import (
    ALLOWED_ROLES,
    ensure_kanban_slot_dir,
    find_wawa_agents,
    kanban_slot_from_agent_id,
    slugify_agent_id,
)
from wawa_openclaw.cli import run_init_agents
from wawa_openclaw.config_io import ensure_agents_tree, load_config
from wawa_openclaw.paths import openclaw_config_path

_PREFIX = "[wkanban] agent add-default: "

_DEFAULT_WAWA_WORKSPACE = Path.home() / ".wawa-kanban" / "workspace"


def _agent_entries(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in cfg.get("agents", {}).get("list", []):
        if isinstance(a, dict) and a.get("id"):
            out.append(a)
    return out


def cmd_agent_add_default(
    *,
    workspace: Path | None = None,
    config: Path | None = None,
    state_dir: Path | None = None,
    repo: Path | None = None,
) -> int:
    """Create default ``agents/`` slot dirs under the Wawa workspace, then run OpenClaw init (all roles)."""
    root = workspace_base(override=workspace)
    if not root.is_dir():
        print(f"{_PREFIX}Workspace not found: {root}", file=sys.stderr)
        return 1
    ensure_init_agent_slot_dirs(root)
    rc = run_init_agents(config=config, state_dir=state_dir, repo=repo, yes=True)
    if rc != 0:
        return rc
    for role in sorted(ALLOWED_ROLES):
        agent_id = slugify_agent_id(f"wawa-{role}")
        slot = kanban_slot_from_agent_id(agent_id)
        ensure_kanban_slot_dir(root, role, slot)
    return 0


def cmd_agent_list(
    *,
    config: Path | None = None,
    long_fmt: bool = False,
    wawa_only: bool = False,
    wawa_workspace: Path | None = None,
) -> int:
    """Print OpenClaw ``agents.list`` entries (sorted by id), one per line."""
    path = config or openclaw_config_path()
    cfg = load_config(path)
    ensure_agents_tree(cfg)
    entries = _agent_entries(cfg)

    if wawa_only:
        ws = (
            wawa_workspace.expanduser().resolve()
            if wawa_workspace is not None
            else _DEFAULT_WAWA_WORKSPACE.resolve()
        )
        allowed = set(find_wawa_agents(cfg, ws))
        entries = [e for e in entries if e.get("id") in allowed]

    entries.sort(key=lambda e: str(e.get("id", "")))

    if not entries:
        print("No agents.")
        return 0

    for e in entries:
        aid = str(e["id"])
        if long_fmt:
            name = e.get("name")
            print(f"{aid}\t{name if name is not None else ''}")
        else:
            print(aid)
    return 0
