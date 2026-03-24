"""Entry point for ``uv run wkanban`` / ``python -m wawa_cli``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wawa_cli import agent_commands, project_commands
from wawa_openclaw.cli import add_agent_add_arguments, add_agent_remove_arguments, run_add, run_remove


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wkanban",
        description="Wawa Kanban CLI (agent and workspace project helpers).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- agent ---
    agent_p = sub.add_parser("agent", help="OpenClaw agent registration, listing, and removal.")
    agent_sub = agent_p.add_subparsers(dest="agent_cmd", required=True)

    add_p = agent_sub.add_parser(
        "add",
        help="Register a new OpenClaw agent (openclaw.json + workspace + role templates).",
    )
    add_agent_add_arguments(add_p)

    remove_p = agent_sub.add_parser(
        "remove",
        help="Remove an agent from openclaw.json (optional --purge to delete dirs).",
    )
    add_agent_remove_arguments(remove_p)

    list_ag_p = agent_sub.add_parser(
        "list",
        help="List agents from openclaw.json agents.list (sorted by id).",
    )
    list_ag_p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    list_ag_p.add_argument(
        "--long",
        action="store_true",
        help="Print id and display name separated by a tab.",
    )
    list_ag_p.add_argument(
        "--wawa-only",
        action="store_true",
        help="Only agents with id prefix wawa- whose workspace path lies under the Wawa workspace.",
    )
    list_ag_p.add_argument(
        "--wawa-workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help="With --wawa-only: Wawa workspace root (default: ~/.wawa-kanban/workspace).",
    )

    add_def_p = agent_sub.add_parser(
        "add-default",
        help=(
            "Create default kanban agent slot dirs under the Wawa workspace (same as wkanban init) "
            "and register every Wawa role in OpenClaw (same as openclaw-init-agents)."
        ),
    )
    add_def_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains agents/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )
    add_def_p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    add_def_p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    add_def_p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )

    # --- project ---
    proj_p = sub.add_parser("project", help="Workspace projects under WAWA_WORKSPACE_PATH/projects/.")
    proj_sub = proj_p.add_subparsers(dest="project_cmd", required=True)

    add_proj_p = proj_sub.add_parser(
        "add",
        help="Create a new project under projects/ (same dirs as wkanban init: todos, waiting_for_verification, finished).",
    )
    add_proj_p.add_argument(
        "name",
        help=(
            "Project slug or full id (e.g. my-app -> wawa.proj.my-app, "
            "or pass wawa.proj.my-app)."
        ),
    )
    add_proj_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains projects/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )
    add_proj_p.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    proj_sub.add_parser("archive", help="Archive a project (not implemented).")
    list_p = proj_sub.add_parser(
        "list",
        help="List project directory names (one per line).",
    )
    list_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains projects/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "agent":
        if args.agent_cmd == "add":
            return run_add(args)
        if args.agent_cmd == "remove":
            return run_remove(args)
        if args.agent_cmd == "list":
            return agent_commands.cmd_agent_list(
                config=getattr(args, "config", None),
                long_fmt=bool(getattr(args, "long", False)),
                wawa_only=bool(getattr(args, "wawa_only", False)),
                wawa_workspace=getattr(args, "wawa_workspace", None),
            )
        if args.agent_cmd == "add-default":
            return agent_commands.cmd_agent_add_default(
                workspace=getattr(args, "workspace", None),
                config=getattr(args, "config", None),
                state_dir=getattr(args, "state_dir", None),
                repo=getattr(args, "repo", None),
            )
        raise AssertionError(f"unexpected agent_cmd: {args.agent_cmd!r}")

    if args.command == "project":
        if args.project_cmd == "add":
            return project_commands.cmd_project_add(
                args.name,
                workspace=getattr(args, "workspace", None),
                yes=bool(getattr(args, "yes", False)),
            )
        if args.project_cmd == "archive":
            return project_commands.cmd_project_archive()
        if args.project_cmd == "list":
            return project_commands.cmd_project_list(workspace=getattr(args, "workspace", None))
        raise AssertionError(f"unexpected project_cmd: {args.project_cmd!r}")

    raise AssertionError(f"unexpected command: {args.command!r}")
