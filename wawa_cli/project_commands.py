"""Workspace project subcommands (add / archive / list).

``add`` creates the same per-project directory tree as ``wkanban init`` /
``install.sh`` / ``cli/wkanban`` ``ensure_dirs``: ``todos``, ``waiting_for_verification``,
and ``finished`` under ``projects/<project_id>/`` (directories only).
``archive`` is still a stub.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from wawa_cli.workspace_paths import projects_dir, workspace_base

# Same column dirs as ``cli/wkanban`` ``ensure_dirs`` / ``install.sh`` for the default project.
_INIT_PROJECT_COLUMN_DIRS = (
    "todos",
    "waiting_for_verification",
    "finished",
)

_PROJECT_ID_PREFIX = "wawa.proj."

STUB_EXIT_CODE = 3
STUB_PREFIX = "[wkanban] project "


def _project_id_from_arg(name: str) -> str:
    """Build project directory id: ``wawa.proj.<slug>`` or accept full ``wawa.proj.*``."""
    s = name.strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        raise ValueError("Invalid project name.")
    if s.startswith(_PROJECT_ID_PREFIX):
        rest = s[len(_PROJECT_ID_PREFIX) :]
        if not rest or not re.match(r"^[a-z0-9][a-z0-9.-]*$", rest):
            raise ValueError("Invalid project id after wawa.proj.")
        return s
    slug = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if not slug or not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise ValueError("Invalid project name; use letters, numbers, and hyphens.")
    return f"{_PROJECT_ID_PREFIX}{slug}"


def _project_init_layout_complete(project_dir: Path) -> bool:
    return project_dir.is_dir() and all(
        (project_dir / sub).is_dir() for sub in _INIT_PROJECT_COLUMN_DIRS
    )


def _confirm_create(message: str, *, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    try:
        reply = input(f"{message} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("y", "yes")


def cmd_project_add(
    name: str,
    *,
    workspace: Path | None = None,
    yes: bool = False,
) -> int:
    """Create project layout under ``projects/<project_id>/`` after optional y/n prompt."""
    try:
        project_id = _project_id_from_arg(name)
    except ValueError as e:
        print(f"{STUB_PREFIX}add: {e}", file=sys.stderr)
        return 1

    root = workspace_base(override=workspace)
    if not root.is_dir():
        print(f"{STUB_PREFIX}add: Workspace not found: {root}", file=sys.stderr)
        return 1

    pdir = projects_dir(root)
    target = pdir / project_id
    if target.is_file():
        print(f"{STUB_PREFIX}add: Path exists and is not a directory: {target}", file=sys.stderr)
        return 1
    if target.is_dir():
        if _project_init_layout_complete(target):
            print(f"Project already present: {target} (skipped)")
            return 0
        pdir.mkdir(parents=True, exist_ok=True)
        for sub in _INIT_PROJECT_COLUMN_DIRS:
            (target / sub).mkdir(parents=True, exist_ok=True)
        print(f"Updated project layout: {target}")
        return 0

    cols = ", ".join(_INIT_PROJECT_COLUMN_DIRS)
    prompt = (
        f"Create project '{project_id}' under {pdir} with column directories ({cols}) "
        f"(same layout as wkanban init)?"
    )
    if not _confirm_create(prompt, assume_yes=yes):
        print("Aborted.", file=sys.stderr)
        return 1

    pdir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"{STUB_PREFIX}add: Project already exists: {target}", file=sys.stderr)
        return 1

    # Mirror ``mkdir -p .../todos .../waiting_for_verification .../finished`` (init layout).
    for sub in _INIT_PROJECT_COLUMN_DIRS:
        (target / sub).mkdir(parents=True, exist_ok=True)
    print(f"Created {target}")
    return 0


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
