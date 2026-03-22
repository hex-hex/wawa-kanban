"""Workspace project subcommands (add / archive / list).

Planned behavior (not implemented yet):
- add: create ``wawa.proj.<slug>/`` under ``<workspace>/projects/`` with column dirs
  (todos, waiting_for_verification, finished, …) and optional ``project.md``.
- archive: move or mark projects as archived (strategy TBD with UI scanning).
- list: print project ids under ``projects/`` (implemented).
"""

from __future__ import annotations

import sys
from pathlib import Path

from wawa_cli.workspace_paths import projects_dir, workspace_base


STUB_EXIT_CODE = 3
STUB_PREFIX = "[wkanban] project "


def cmd_project_add(_argv: list[str] | None = None) -> int:
    """Placeholder for ``wkanban project add``."""
    print(f"{STUB_PREFIX}add: Not implemented yet.", file=sys.stderr)
    return STUB_EXIT_CODE


def cmd_project_archive(_argv: list[str] | None = None) -> int:
    """Placeholder for ``wkanban project archive``."""
    print(f"{STUB_PREFIX}archive: Not implemented yet.", file=sys.stderr)
    return STUB_EXIT_CODE


def cmd_project_list(workspace: Path | None = None) -> int:
    """List project ids (subdirectory names under ``projects/``), one per line."""
    root = workspace_base(override=workspace)
    pdir = projects_dir(root)
    if not root.is_dir():
        print(f"{STUB_PREFIX}list: Workspace not found: {root}", file=sys.stderr)
        return 1
    if not pdir.is_dir():
        print(f"{STUB_PREFIX}list: Projects directory not found: {pdir}", file=sys.stderr)
        return 1

    names = sorted(
        x.name
        for x in pdir.iterdir()
        if x.is_dir() and not x.name.startswith(".")
    )
    if not names:
        print("No projects.")
        return 0
    for name in names:
        print(name)
    return 0
