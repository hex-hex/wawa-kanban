"""Todo listing commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from wawa_cli.workspace_paths import projects_dir, workspace_base

TODO_PREFIX = "[wkanban] todo "
_PROJECT_ID_PREFIX = "wawa.proj."


def _iter_todo_md_files(root: Path) -> list[Path]:
    result: list[Path] = []
    if not root.is_dir():
        return result
    pdir = projects_dir(root)
    if not pdir.is_dir():
        return result
    for proj in sorted([p for p in pdir.iterdir() if p.is_dir() and not p.name.startswith(".")], key=lambda p: p.name):
        todo = proj / "todos"
        if not todo.is_dir():
            continue
        for f in sorted(todo.iterdir(), key=lambda x: x.name):
            if not f.is_file():
                continue
            if not f.name.endswith(".md") or f.name.endswith(".md.lock"):
                continue
            result.append(f)
    return sorted(result, key=lambda p: (p.stat().st_ctime, p.name))


def _display_ticket_name(path: Path) -> str:
    # Input: wawa.proj.<project>.<mode>.<slug>.md
    stem = path.name[:-3]  # strip ".md"
    parts = stem.split(".")
    if len(parts) < 5 or parts[0] != "wawa" or parts[1] != "proj":
        return stem
    project_name = parts[2]
    slug = ".".join(parts[4:])
    return f"{project_name}.{slug}"


def _project_location_for(path: Path) -> str:
    proj_dir = path.parent.parent
    loc = proj_dir / ".project.location"
    if not loc.is_file():
        return ""
    raw = loc.read_text(encoding="utf-8").strip()
    return raw


def cmd_todo_list(*, workspace: Path | None = None) -> int:
    root = workspace_base(override=workspace)
    if not root.is_dir():
        print(f"{TODO_PREFIX}list: Workspace not found: {root}")
        return 1

    files = _iter_todo_md_files(root)
    if not files:
        print("No todos.")
        return 0

    for f in files:
        name = _display_ticket_name(f)
        created = datetime.fromtimestamp(f.stat().st_ctime).isoformat(timespec="seconds")
        loc = _project_location_for(f)
        if loc:
            print(f"{name}\t{created}\t{loc}")
        else:
            print(f"{name}\t{created}")
    return 0

