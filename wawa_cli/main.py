"""Entry point for ``uv run wkanban`` / ``python -m wawa_cli``."""

from __future__ import annotations

import argparse
import sys

from wawa_cli import project_commands
from wawa_openclaw.cli import add_agent_add_arguments, add_agent_remove_arguments, run_add, run_remove


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wkanban",
        description="Wawa Kanban CLI (agent and workspace project helpers).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- agent ---
    agent_p = sub.add_parser("agent", help="OpenClaw agent registration and removal.")
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

    # --- project (stubs) ---
    proj_p = sub.add_parser("project", help="Workspace projects (stubs; see project_commands).")
    proj_sub = proj_p.add_subparsers(dest="project_cmd", required=True)

    proj_sub.add_parser("add", help="Create a new project directory (not implemented).")
    proj_sub.add_parser("archive", help="Archive a project (not implemented).")
    proj_sub.add_parser("list", help="List projects (not implemented).")

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
        raise AssertionError(f"unexpected agent_cmd: {args.agent_cmd!r}")

    if args.command == "project":
        if args.project_cmd == "add":
            return project_commands.cmd_project_add()
        if args.project_cmd == "archive":
            return project_commands.cmd_project_archive()
        if args.project_cmd == "list":
            return project_commands.cmd_project_list()
        raise AssertionError(f"unexpected project_cmd: {args.project_cmd!r}")

    raise AssertionError(f"unexpected command: {args.command!r}")
