from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wawa_openclaw.agents_ops import (
    ALLOWED_ROLES,
    materialize_agent,
    merge_agent_into_config,
    plan_add_agent,
    purge_agent_paths,
    remove_agent_from_config,
    slugify_agent_id,
)
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config
from wawa_openclaw.paths import openclaw_config_path, openclaw_state_dir, repo_root


def _parser_add() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Register a new OpenClaw agent: append to openclaw.json, create workspace and agentDir, "
            "and copy role templates from this repo's agents/<role>/."
        )
    )
    p.add_argument("name", help="Display name; used to derive agent id (slug).")
    p.add_argument(
        "--role",
        required=True,
        choices=sorted(ALLOWED_ROLES),
        help="Template folder under agents/ in the Wawa Kanban repo.",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )
    return p


def _parser_remove() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Remove an agent created by openclaw-agent-add from openclaw.json (and optional disk purge)."
    )
    p.add_argument("name", help="Same name as used for add; id is derived by slug.")
    p.add_argument(
        "--purge",
        action="store_true",
        help="Delete workspace-wawa-<id> and ~/.openclaw/agents/<id>/ after removing from config.",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="With --purge, skip confirmation.",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    return p


def main_add(argv: list[str] | None = None) -> int:
    try:
        args = _parser_add().parse_args(argv)
        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        root = args.repo or repo_root()

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)

        entry, workspace, agent_dir, role_src = plan_add_agent(
            name=args.name, role=args.role, root=root, state=state
        )
        merge_agent_into_config(cfg, entry)
        save_config(config_path, cfg)
        materialize_agent(workspace=workspace, agent_dir=agent_dir, role_src=role_src)

        print(f"Added agent id={entry['id']!r}")
        print(f"  workspace: {workspace}")
        print(f"  agentDir:  {agent_dir}")
        print(f"  config:    {config_path}")
        print(
            "Mount this OpenClaw home in Docker, e.g. -v ~/.openclaw:/root/.openclaw "
            "(adjust user path inside the container)."
        )
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main_remove(argv: list[str] | None = None) -> int:
    try:
        args = _parser_remove().parse_args(argv)
        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        agent_id = slugify_agent_id(args.name)

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)
        remove_agent_from_config(cfg, agent_id)
        save_config(config_path, cfg)
        print(f"Removed agent id={agent_id!r} from {config_path}")

        if args.purge:
            if not args.yes:
                ws = state / f"workspace-wawa-{agent_id}"
                ar = state / "agents" / agent_id
                print(f"Will delete:\n  {ws}\n  {ar}")
                confirm = input("Type yes to delete: ").strip().lower()
                if confirm != "yes":
                    print("Aborted; config updated but files kept.")
                    return 0
            purge_agent_paths(agent_id, state=state)
            print("Purged workspace and agentDir.")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    print("Use openclaw-agent-add or openclaw-agent-remove.", file=sys.stderr)
    return 2
