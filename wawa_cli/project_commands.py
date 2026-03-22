"""Workspace project subcommands (add / archive / list).

Planned behavior (not implemented yet):
- add: create ``wawa.proj.<slug>/`` under ``<workspace>/projects/`` with column dirs
  (todos, waiting_for_verification, finished, …) and optional ``project.md``.
- archive: move or mark projects as archived (strategy TBD with UI scanning).
- list: print project ids under ``projects/``.
"""

from __future__ import annotations

import sys


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


def cmd_project_list(_argv: list[str] | None = None) -> int:
    """Placeholder for ``wkanban project list``."""
    print(f"{STUB_PREFIX}list: Not implemented yet.", file=sys.stderr)
    return STUB_EXIT_CODE
