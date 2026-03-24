from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wawa_openclaw.agents_ops import (
    ALLOWED_ROLES,
    find_wawa_agents,
    materialize_agent,
    merge_agent_into_config,
    plan_add_agent,
    purge_agent_paths,
    remove_agent_from_config,
    slugify_agent_id,
)
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config
from wawa_openclaw.paths import openclaw_config_path, openclaw_state_dir, repo_root


def add_agent_add_arguments(p: argparse.ArgumentParser) -> None:
    """Register OpenClaw agent-add CLI arguments on an existing parser (for nested wkanban CLI)."""
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


def _parser_add() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Register a new OpenClaw agent: append to openclaw.json, create workspace and agentDir, "
            "and copy role templates from this repo's agents/<role>/."
        )
    )
    add_agent_add_arguments(p)
    return p


def add_agent_remove_arguments(p: argparse.ArgumentParser) -> None:
    """Register OpenClaw agent-remove CLI arguments on an existing parser (for nested wkanban CLI)."""
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


def _parser_remove() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Remove an agent created by openclaw-agent-add from openclaw.json (and optional disk purge)."
    )
    add_agent_remove_arguments(p)
    return p


def run_add(args: argparse.Namespace) -> int:
    """Execute agent add from a parsed argparse Namespace (shared by main_add and wawa_cli)."""
    try:
        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        root = args.repo or repo_root()

        name = args.name if args.name.startswith("wawa-") else f"wawa-{args.name}"

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)

        entry, workspace, agent_dir, role_src = plan_add_agent(
            name=name, role=args.role, root=root, state=state
        )
        merge_agent_into_config(cfg, entry)
        save_config(config_path, cfg)
        materialize_agent(workspace=workspace, agent_dir=agent_dir, role_src=role_src)

        print(f"Added agent name={name!r} id={entry['id']!r}")
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


def main_add(argv: list[str] | None = None) -> int:
    args = _parser_add().parse_args(argv)
    return run_add(args)


def run_remove(args: argparse.Namespace) -> int:
    """Execute agent remove from a parsed argparse Namespace (shared by main_remove and wawa_cli)."""
    try:
        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        # Match run_add: same display name → same derived id (wawa- prefix when omitted).
        display_name = args.name if args.name.startswith("wawa-") else f"wawa-{args.name}"
        agent_id = slugify_agent_id(display_name)

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


def main_remove(argv: list[str] | None = None) -> int:
    args = _parser_remove().parse_args(argv)
    return run_remove(args)


def _parser_init_agents() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Register all default Wawa agents (one per role) into openclaw.json. "
            "Each agent is named 'wawa-<role>'. Already-registered agents are skipped."
        )
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


def run_init_agents(
    *,
    config: Path | None = None,
    state_dir: Path | None = None,
    repo: Path | None = None,
) -> int:
    """Register all default Wawa agents (one per role). Same behavior as ``openclaw-init-agents``."""
    config_path = config or openclaw_config_path()
    state = state_dir or openclaw_state_dir()
    root = repo or repo_root()

    cfg = load_config(config_path)
    ensure_agents_tree(cfg)

    errors = 0
    for role in sorted(ALLOWED_ROLES):
        name = f"wawa-{role}"
        try:
            entry, workspace, agent_dir, role_src = plan_add_agent(
                name=name, role=role, root=root, state=state
            )
            merge_agent_into_config(cfg, entry)
            save_config(config_path, cfg)
            materialize_agent(workspace=workspace, agent_dir=agent_dir, role_src=role_src)
            print(f"  [added]   {name} (role={role})")
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                print(f"  [skipped] {name} (already registered)")
            else:
                print(f"  [error]   {name}: {msg}", file=sys.stderr)
                errors += 1

    print(f"Done. Config: {config_path}")
    return 1 if errors else 0


def main_init_agents(argv: list[str] | None = None) -> int:
    args = _parser_init_agents().parse_args(argv)
    return run_init_agents(
        config=args.config,
        state_dir=args.state_dir,
        repo=args.repo,
    )


def _parser_uninstall_agents() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Remove all Wawa-managed agents from openclaw.json. "
            "Only agents whose id starts with 'wawa-' AND whose workspace is under "
            "the Wawa workspace directory are removed."
        )
    )
    p.add_argument(
        "--wawa-workspace",
        type=Path,
        default=Path.home() / ".wawa-kanban" / "workspace",
        help="Wawa workspace root used to verify agent ownership (default: ~/.wawa-kanban/workspace).",
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


def main_uninstall_agents(argv: list[str] | None = None) -> int:
    args = _parser_uninstall_agents().parse_args(argv)
    config_path = args.config or openclaw_config_path()
    state = args.state_dir or openclaw_state_dir()

    cfg = load_config(config_path)
    if not cfg:
        print("No openclaw.json found, nothing to clean up.")
        return 0

    agent_ids = find_wawa_agents(cfg, args.wawa_workspace)
    if not agent_ids:
        print("No Wawa-managed agents found in openclaw.json.")
        return 0

    for agent_id in agent_ids:
        remove_agent_from_config(cfg, agent_id)
        purge_agent_paths(agent_id, state=state)
        print(f"  [removed] {agent_id}")

    save_config(config_path, cfg)
    print(f"Done. Removed {len(agent_ids)} agent(s) from {config_path}")
    return 0


def main() -> int:
    print(
        "Use: wkanban agent add|remove|add-default|list, or openclaw-agent-add / "
        "openclaw-agent-remove / openclaw-init-agents / openclaw-uninstall-agents.",
        file=sys.stderr,
    )
    return 2
