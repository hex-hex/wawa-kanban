"""Entry point for ``uv run wkanban`` / ``python -m wawa_cli``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wawa_cli import agent_commands, project_commands, ticket_commands, todo_commands
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
            "and register every Wawa role in OpenClaw."
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

    sync_p = agent_sub.add_parser(
        "sync",
        help="Re-render existing Wawa agents guidance files from latest templates.",
    )
    sync_p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    sync_p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    sync_p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )
    analyze_uninstall_p = agent_sub.add_parser(
        "analyze-uninstall",
        help="Analyze possible uninstall residuals (exit 3 when warnings are found).",
    )
    analyze_uninstall_p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    analyze_uninstall_p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    uninstall_all_p = agent_sub.add_parser(
        "uninstall-all",
        help="Remove all Wawa-managed agents from openclaw.json and purge their state dirs.",
    )
    uninstall_all_p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    uninstall_all_p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
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
    procress_p = proj_sub.add_parser(
        "procress",
        help=(
            "Scan todos + waiting_for_verification and move unlocked .md tickets to free agent slots "
            "(one ticket per agent directory)."
        ),
    )
    procress_p.add_argument(
        "name",
        help=(
            "Project slug or full id (e.g. my-app -> wawa.proj.my-app, "
            "or pass wawa.proj.my-app)."
        ),
    )
    procress_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains projects/ and agents/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )
    procress_p.add_argument(
        "--exec",
        dest="exec_move",
        action="store_true",
        help="Execute file moves. Default is dry-run (print plan only).",
    )

    # --- todo ---
    todo_p = sub.add_parser(
        "todo",
        help="List todo tickets from all projects (projects/*/todos/*.md, excluding .lock).",
    )
    todo_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains projects/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )

    # --- ticket ---
    ticket_p = sub.add_parser("ticket", help="Ticket helpers.")
    ticket_sub = ticket_p.add_subparsers(dest="ticket_cmd", required=True)
    locate_p = ticket_sub.add_parser(
        "locate",
        help="Locate one ticket by <project>.<slug> and output structured info for shell workflows.",
    )
    locate_p.add_argument("target", help="Ticket target in form <project>.<slug> (project may include dots).")
    locate_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Wawa workspace root (contains projects/). "
            "Default: WAWA_WORKSPACE_PATH or ~/.wawa-kanban/workspace."
        ),
    )
    locate_p.add_argument(
        "--format",
        choices=("json", "shell"),
        default="json",
        help="Output format for automation. 'shell' prints key<TAB>value lines.",
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
        if args.agent_cmd == "sync":
            return agent_commands.cmd_agent_sync(
                config=getattr(args, "config", None),
                state_dir=getattr(args, "state_dir", None),
                repo=getattr(args, "repo", None),
            )
        if args.agent_cmd == "analyze-uninstall":
            return agent_commands.cmd_agent_analyze_uninstall(
                config=getattr(args, "config", None),
                state_dir=getattr(args, "state_dir", None),
            )
        if args.agent_cmd == "uninstall-all":
            return agent_commands.cmd_agent_uninstall_all(
                config=getattr(args, "config", None),
                state_dir=getattr(args, "state_dir", None),
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
        if args.project_cmd == "procress":
            return project_commands.cmd_project_procress(
                args.name,
                workspace=getattr(args, "workspace", None),
                exec_move=bool(getattr(args, "exec_move", False)),
            )
        raise AssertionError(f"unexpected project_cmd: {args.project_cmd!r}")

    if args.command == "todo":
        return todo_commands.cmd_todo_list(workspace=getattr(args, "workspace", None))

    if args.command == "ticket":
        if args.ticket_cmd == "locate":
            return ticket_commands.cmd_ticket_locate(
                args.target,
                workspace=getattr(args, "workspace", None),
                fmt=getattr(args, "format", "json"),
            )
        raise AssertionError(f"unexpected ticket_cmd: {args.ticket_cmd!r}")

    raise AssertionError(f"unexpected command: {args.command!r}")
