"""Workspace project subcommands (add / archive / list / procress).

``add`` creates the same per-project directory tree as ``wkanban init`` /
``install.sh`` / ``cli/wkanban.sh`` ``ensure_dirs``: ``todos``, ``waiting_for_verification``,
and ``finished`` under ``projects/<project_id>/`` (directories only).
``archive`` is still a stub.
``add`` also creates empty metadata files: ``project.md`` and ``.project.location``.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from wawa_cli.workspace_paths import projects_dir, workspace_base

# Same column dirs as ``cli/wkanban.sh`` ``ensure_dirs`` / ``install.sh`` for the default project.
_INIT_PROJECT_COLUMN_DIRS = (
    "todos",
    "waiting_for_verification",
    "finished",
)

_PROJECT_ID_PREFIX = "wawa.proj."

STUB_EXIT_CODE = 3
STUB_PREFIX = "[wkanban] project "

_MODE_TO_TODO_AGENT_TYPE: dict[str, str] = {
    "implementation": "developers",
    "codesearch": "developers",
    "design": "designers",
    "websearch": "info-officers",
}

_MODE_TO_VERIFY_AGENT_TYPE: dict[str, str] = {
    "implementation": "code-verifiers",
    "codesearch": "code-verifiers",
    "design": "general-verifiers",
    "websearch": "general-verifiers",
}


def _iter_ticket_files_sorted_by_ctime(directory: Path) -> list[Path]:
    """Return unlocked ``.md`` ticket files sorted by create/change time then name."""
    if not directory.is_dir():
        return []
    items = [
        p
        for p in directory.iterdir()
        if p.is_file()
        and p.name.endswith(".md")
        and not p.name.endswith(".md.lock")
        and p.name.startswith(_PROJECT_ID_PREFIX)
    ]
    return sorted(items, key=lambda p: (p.stat().st_ctime, p.name))


def _ticket_mode_from_filename(path: Path) -> str | None:
    # Format: {project_id}.{mode}.{slug}.md, where project_id contains two dots.
    name = path.name
    if not name.endswith(".md"):
        return None
    parts = name[:-3].split(".")
    if len(parts) < 4:
        return None
    # wawa.proj.<name>.<mode>.<slug...>
    return parts[3]


def _is_agent_slot_busy(slot_dir: Path) -> bool:
    if not slot_dir.is_dir():
        return False
    return any(
        p.is_file()
        and p.name.startswith(_PROJECT_ID_PREFIX)
        and (p.name.endswith(".md") or p.name.endswith(".md.lock"))
        for p in slot_dir.iterdir()
    )


def _move_one_ticket_to_first_free_slot(
    agents_root: Path,
    target_type: str,
    reserved_slots: set[Path] | None = None,
) -> Path | None:
    reserved_slots = reserved_slots or set()
    type_root = agents_root / target_type
    if not type_root.is_dir():
        return None
    for slot in sorted([p for p in type_root.iterdir() if p.is_dir()], key=lambda p: p.name):
        if slot in reserved_slots:
            continue
        if _is_agent_slot_busy(slot):
            continue
        return slot
    return None


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


def _confirm_create(message: str, *, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    try:
        reply = input(f"{message} [Y/n]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("", "y", "yes")


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
    if target.exists():
        print(
            f"{STUB_PREFIX}add: Project path already exists (duplicate): {target}. Refusing to create.",
            file=sys.stderr,
        )
        return 1

    cols = ", ".join(_INIT_PROJECT_COLUMN_DIRS)
    prompt = (
        f"Create project '{project_id}' under {pdir} with column directories ({cols}) "
        f"(same layout as wkanban init)?"
    )
    if not yes and not sys.stdin.isatty():
        print(
            f"{STUB_PREFIX}add: stdin is not a TTY; pass --yes to create without a prompt.",
            file=sys.stderr,
        )
        return 1
    if not _confirm_create(prompt, assume_yes=yes):
        print("Aborted.", file=sys.stderr)
        return 1

    pdir.mkdir(parents=True, exist_ok=True)

    # Mirror ``mkdir -p .../todos .../waiting_for_verification .../finished`` (init layout).
    for sub in _INIT_PROJECT_COLUMN_DIRS:
        (target / sub).mkdir(parents=True, exist_ok=True)
    # Keep parity with documented workspace shape: create empty project metadata files.
    (target / "project.md").touch(exist_ok=True)
    (target / ".project.location").touch(exist_ok=True)
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


def cmd_project_procress(name: str, *, workspace: Path | None = None, exec_move: bool = False) -> int:
    """Dispatch unlocked tickets from project pending columns to free agent slot dirs."""
    try:
        project_id = _project_id_from_arg(name)
    except ValueError as e:
        print(f"{STUB_PREFIX}procress: {e}", file=sys.stderr)
        return 1

    root = workspace_base(override=workspace)
    if not root.is_dir():
        print(f"{STUB_PREFIX}procress: Workspace not found: {root}", file=sys.stderr)
        return 1

    project_root = projects_dir(root) / project_id
    if not project_root.is_dir():
        print(f"{STUB_PREFIX}procress: Project not found: {project_root}", file=sys.stderr)
        return 1

    agents_root = root / "agents"
    if not agents_root.is_dir():
        print(f"{STUB_PREFIX}procress: Agents directory not found: {agents_root}", file=sys.stderr)
        return 1

    planned = 0
    moved = 0
    skipped_unknown_mode = 0
    skipped_no_free_slot = 0
    reserved_slots: set[Path] = set()

    # 1) todos -> working agents by ticket mode
    for ticket in _iter_ticket_files_sorted_by_ctime(project_root / "todos"):
        mode = _ticket_mode_from_filename(ticket)
        target_type = _MODE_TO_TODO_AGENT_TYPE.get(mode or "")
        if target_type is None:
            skipped_unknown_mode += 1
            continue
        slot = _move_one_ticket_to_first_free_slot(agents_root, target_type, reserved_slots)
        if slot is None:
            skipped_no_free_slot += 1
            continue
        planned += 1
        reserved_slots.add(slot)
        dest = slot / ticket.name
        print(f"PLAN: {ticket} -> {dest}")
        if exec_move:
            shutil.move(str(ticket), str(dest))
            moved += 1

    # 2) waiting_for_verification -> verifier agents by ticket mode
    for ticket in _iter_ticket_files_sorted_by_ctime(project_root / "waiting_for_verification"):
        mode = _ticket_mode_from_filename(ticket)
        target_type = _MODE_TO_VERIFY_AGENT_TYPE.get(mode or "")
        if target_type is None:
            skipped_unknown_mode += 1
            continue
        slot = _move_one_ticket_to_first_free_slot(agents_root, target_type, reserved_slots)
        if slot is None:
            skipped_no_free_slot += 1
            continue
        planned += 1
        reserved_slots.add(slot)
        dest = slot / ticket.name
        print(f"PLAN: {ticket} -> {dest}")
        if exec_move:
            shutil.move(str(ticket), str(dest))
            moved += 1

    print(
        f"Processed {project_id}: dry_run={'no' if exec_move else 'yes'} planned={planned} moved={moved} "
        f"skipped_unknown_mode={skipped_unknown_mode} skipped_no_free_slot={skipped_no_free_slot}"
    )
    return 0
