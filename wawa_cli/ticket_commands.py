"""Ticket helper commands used by host shell workflows."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from wawa_cli.workspace_paths import projects_dir, workspace_base

_PROJECT_ID_PREFIX = "wawa.proj."
_TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z0-9][a-z0-9-]*$")
_WARN_NON_IMPLEMENTATION = "ticket mode is not implementation; worktree not required"
_WARN_REPO_MISSING = "target repo from .project.location does not exist"
_WARN_NOT_GIT = "target repo from .project.location is not a git repository"
_WARN_LOCATION_EMPTY = ".project.location is empty"


def _parse_target(target: str) -> tuple[str, str]:
    s = target.strip()
    if not s or not _TARGET_RE.match(s):
        raise ValueError("target must be '<project>.<slug>' (letters/numbers/hyphen; project may include dots)")
    project_part, slug = s.rsplit(".", 1)
    if project_part.startswith(_PROJECT_ID_PREFIX):
        project_suffix = project_part[len(_PROJECT_ID_PREFIX) :]
    else:
        project_suffix = project_part
    if not project_suffix:
        raise ValueError("project part in target cannot be empty")
    return f"{_PROJECT_ID_PREFIX}{project_suffix}", slug


def _iter_ticket_candidates(project_root: Path, project_id: str, slug: str) -> list[Path]:
    if not project_root.is_dir():
        return []
    pattern = f"{project_id}.*.{slug}.md"
    found = [p for p in project_root.rglob(pattern) if p.is_file() and not p.name.endswith(".md.lock")]
    # Keep ticket columns only; ignore metadata docs.
    allowed_parent_names = {"todos", "waiting_for_verification", "finished"}
    return sorted([p for p in found if p.parent.name in allowed_parent_names], key=lambda p: str(p))


def _mode_and_slug_from_filename(path: Path, project_id: str) -> tuple[str, str] | None:
    name = path.name
    if not name.endswith(".md"):
        return None
    stem = name[:-3]
    prefix = f"{project_id}."
    if not stem.startswith(prefix):
        return None
    rest = stem[len(prefix) :]
    parts = rest.split(".", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def _is_git_repo(path: Path) -> bool:
    cp = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return cp.returncode == 0 and cp.stdout.strip() == "true"


def _emit(
    *,
    fmt: str,
    status: str,
    message: str,
    project_id: str,
    slug: str,
    mode: str = "",
    ticket_path: str = "",
    project_dir: str = "",
    project_location_file: str = "",
    repo_path: str = "",
    target_worktree: str = "",
    target_branch: str = "",
) -> None:
    payload = {
        "status": status,
        "message": message,
        "project_id": project_id,
        "slug": slug,
        "mode": mode,
        "ticket_path": ticket_path,
        "project_dir": project_dir,
        "project_location_file": project_location_file,
        "repo_path": repo_path,
        "target_worktree": target_worktree,
        "target_branch": target_branch,
    }
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=True))
        return
    for k, v in payload.items():
        print(f"{k}\t{v}")


def cmd_ticket_locate(target: str, *, workspace: Path | None = None, fmt: str = "json") -> int:
    try:
        project_id, slug = _parse_target(target)
    except ValueError as e:
        print(f"[wkanban] ticket locate: {e}", file=sys.stderr)
        return 1

    root = workspace_base(override=workspace)
    pdir = projects_dir(root)
    project_root = pdir / project_id
    if not root.is_dir():
        print(f"[wkanban] ticket locate: Workspace not found: {root}", file=sys.stderr)
        return 1
    if not project_root.is_dir():
        print(f"[wkanban] ticket locate: Project not found: {project_root}", file=sys.stderr)
        return 1

    candidates = _iter_ticket_candidates(project_root, project_id, slug)
    if not candidates:
        print(f"[wkanban] ticket locate: No ticket matched target: {target}", file=sys.stderr)
        return 1
    if len(candidates) > 1:
        print(
            "[wkanban] ticket locate: Target matched multiple tickets; use a unique slug.\n"
            + "\n".join(f"  - {p}" for p in candidates),
            file=sys.stderr,
        )
        return 1

    ticket_path = candidates[0].resolve()
    parsed = _mode_and_slug_from_filename(ticket_path, project_id)
    if parsed is None:
        print(f"[wkanban] ticket locate: Unsupported ticket filename format: {ticket_path.name}", file=sys.stderr)
        return 1
    mode, _slug_from_file = parsed
    loc_file = (project_root / ".project.location").resolve()
    loc_raw = loc_file.read_text(encoding="utf-8").strip() if loc_file.is_file() else ""

    if mode != "implementation":
        _emit(
            fmt=fmt,
            status="warning",
            message=_WARN_NON_IMPLEMENTATION,
            project_id=project_id,
            slug=slug,
            mode=mode,
            ticket_path=str(ticket_path),
            project_dir=str(project_root.resolve()),
            project_location_file=str(loc_file),
        )
        return 0

    if not loc_raw:
        _emit(
            fmt=fmt,
            status="warning",
            message=_WARN_LOCATION_EMPTY,
            project_id=project_id,
            slug=slug,
            mode=mode,
            ticket_path=str(ticket_path),
            project_dir=str(project_root.resolve()),
            project_location_file=str(loc_file),
        )
        return 0

    repo_path = Path(loc_raw).expanduser().resolve()
    if not repo_path.exists():
        _emit(
            fmt=fmt,
            status="warning",
            message=_WARN_REPO_MISSING,
            project_id=project_id,
            slug=slug,
            mode=mode,
            ticket_path=str(ticket_path),
            project_dir=str(project_root.resolve()),
            project_location_file=str(loc_file),
            repo_path=str(repo_path),
        )
        return 0
    if not _is_git_repo(repo_path):
        _emit(
            fmt=fmt,
            status="warning",
            message=_WARN_NOT_GIT,
            project_id=project_id,
            slug=slug,
            mode=mode,
            ticket_path=str(ticket_path),
            project_dir=str(project_root.resolve()),
            project_location_file=str(loc_file),
            repo_path=str(repo_path),
        )
        return 0

    target_worktree = repo_path / ".wawa" / "worktrees" / slug
    target_branch = f"worktree-{slug}"
    _emit(
        fmt=fmt,
        status="ok",
        message="ready",
        project_id=project_id,
        slug=slug,
        mode=mode,
        ticket_path=str(ticket_path),
        project_dir=str(project_root.resolve()),
        project_location_file=str(loc_file),
        repo_path=str(repo_path),
        target_worktree=str(target_worktree),
        target_branch=target_branch,
    )
    return 0

