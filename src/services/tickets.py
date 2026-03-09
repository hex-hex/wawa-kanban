"""Load workspace content (projects, agents) into repository."""

from datetime import datetime
from pathlib import Path

from config import WORKSPACE_PATH, AGENTS_WORKSPACE_PATH, COLUMNS
from src.models.kanban import (
    Ticket,
    TicketStatus,
    TaskMode,
    Project,
    Agent,
    AgentPosition,
)
from src.models.repository import repository
from src.services.workspace import parse_frontmatter, serialize_frontmatter_and_body

# Agent type folder (plural) -> AgentPosition
_TYPE_TO_POSITION: dict[str, AgentPosition] = {
    "testers": AgentPosition.TESTER,
    "designers": AgentPosition.DESIGNER,
    "developers": AgentPosition.DEVELOPER,
}


def _parse_filename(filename: str) -> tuple[str, TaskMode, str]:
    """Parse ticket filename: {project_id}.{mode}.{slug}.md -> (project_id, mode, slug).
    One format only. Slug is hyphen-separated (no dots). E.g. wawa.proj.default.implementation.setup-project-structure
    """
    stem = filename.replace(".md", "")
    parts = stem.split(".")
    project = parts[0] if parts else ""
    mode = TaskMode.IMPLEMENTATION
    slug = stem

    for i, part in enumerate(parts[1:], 1):
        try:
            mode = TaskMode(part)
            project = ".".join(parts[:i])
            slug = ".".join(parts[i + 1 :]) if i + 1 < len(parts) else ""
            break
        except ValueError:
            continue

    return project, mode, slug


def _load_tickets_from_dir(dir_path: Path, status: TicketStatus) -> list[Ticket]:
    """Load all ticket .md and .md.lock files from a directory."""
    tickets: list[Ticket] = []
    if not dir_path.exists():
        return tickets

    seen_ids: set[str] = set()

    def load_file(md_file: Path, parse_name: str, locked: bool = False) -> None:
        if "placeholder" in md_file.name:
            return
        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)
        project, mode, _ = _parse_filename(parse_name)
        tid = frontmatter.get("id", Path(parse_name).stem)
        if tid in seen_ids:
            return
        seen_ids.add(tid)
        st = md_file.stat()
        created_at = datetime.fromtimestamp(
            getattr(st, "st_birthtime", st.st_mtime)
        ).isoformat()
        updated_at = datetime.fromtimestamp(st.st_mtime).isoformat()
        t: Ticket = {
            "id": tid,
            "title": frontmatter.get("title", Path(parse_name).stem),
            "project": project,
            "description": body,
            "status": status,
            "mode": mode,
            "locked": locked,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        tickets.append(t)

    for lock_file in sorted(dir_path.glob("*.md.lock")):
        load_file(lock_file, lock_file.name.removesuffix(".lock"), locked=True)

    for md_file in sorted(dir_path.glob("*.md")):
        load_file(md_file, md_file.name, locked=False)

    return tickets


PROJECT_NAME_PREFIX = "wawa.proj."


def _find_ticket_file(ticket_id: str) -> Path | None:
    """Find the .md or .md.lock file for a ticket by id (from frontmatter). Searches projects and agents."""
    def check_file(f: Path) -> bool:
        if "placeholder" in f.name:
            return False
        try:
            content = f.read_text()
            frontmatter, _ = parse_frontmatter(content)
            return frontmatter.get("id") == ticket_id
        except OSError:
            return False

    if WORKSPACE_PATH.exists():
        for project_path in sorted(WORKSPACE_PATH.iterdir()):
            if not project_path.is_dir() or project_path.name.startswith("."):
                continue
            for status in COLUMNS:
                col_path = project_path / status.value
                if not col_path.exists():
                    continue
                for pattern in ["*.md", "*.md.lock"]:
                    for f in sorted(col_path.glob(pattern)):
                        if check_file(f):
                            return f
    if AGENTS_WORKSPACE_PATH.exists():
        for type_folder in sorted(AGENTS_WORKSPACE_PATH.iterdir()):
            if not type_folder.is_dir() or type_folder.name.startswith("."):
                continue
            for name_path in sorted(type_folder.iterdir()):
                if not name_path.is_dir():
                    continue
                for pattern in ["*.md", "*.md.lock"]:
                    for f in sorted(name_path.glob(pattern)):
                        if check_file(f):
                            return f
    return None


def get_agent_info(ticket_id: str) -> tuple[AgentPosition, str] | None:
    """If ticket file is under agents/{type}/{name}/, return (position, agent_name)."""
    path = _find_ticket_file(ticket_id)
    if path is None:
        return None
    try:
        rel = path.relative_to(AGENTS_WORKSPACE_PATH)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2:
        return None
    type_folder, agent_name = parts[0], parts[1]
    position = _TYPE_TO_POSITION.get(type_folder)
    if position is None:
        return None
    return (position, agent_name)


def lock_ticket(ticket_id: str) -> bool:
    """Rename ticket .md file to .md.lock. Returns True if successful."""
    path = _find_ticket_file(ticket_id)
    if path is None:
        return False
    if path.name.endswith(".md.lock"):
        return True  # already locked
    if not path.name.endswith(".md"):
        return False
    lock_path = path.with_suffix(path.suffix + ".lock")
    try:
        path.rename(lock_path)
        return True
    except OSError:
        return False


def unlock_ticket(ticket_id: str) -> bool:
    """Rename ticket .md.lock file back to .md. Returns True if successful."""
    path = _find_ticket_file(ticket_id)
    if path is None:
        return False
    if not path.name.endswith(".md.lock"):
        return True  # already unlocked
    md_path = path.with_suffix("")  # removes .lock, leaves .md
    try:
        path.rename(md_path)
        return True
    except OSError:
        return False


def save_ticket_body(ticket_id: str, body: str) -> bool:
    """Write new body to the ticket file. File must be .md.lock (locked). Returns True if successful."""
    path = _find_ticket_file(ticket_id)
    if path is None or not path.name.endswith(".md.lock"):
        return False
    try:
        content = path.read_text()
        frontmatter, _ = parse_frontmatter(content)
        new_content = serialize_frontmatter_and_body(frontmatter, body)
        path.write_text(new_content)
        return True
    except OSError:
        return False


def _display_name(project_id: str) -> str:
    """Return project name for UI: strip prefix 'wawa.proj.' if present."""
    if project_id.startswith(PROJECT_NAME_PREFIX):
        return project_id[len(PROJECT_NAME_PREFIX) :]
    return project_id


def _load_project(project_path: Path) -> Project | None:
    """Load a single project from workspace/projects/{project_id}/.
    Verifying column also includes tickets from workspace/agents/testers/*."""
    project_id = project_path.name
    if project_id.startswith("."):
        return None

    tickets: list[Ticket] = []
    for status in COLUMNS:
        if status == TicketStatus.IN_PROGRESS:
            continue  # In Progress comes from developers/designers agents only
        if status == TicketStatus.VERIFYING:
            continue  # Verifying comes from agents/testers only, not projects
        col_path = project_path / status.value
        tickets.extend(_load_tickets_from_dir(col_path, status))

    existing_ids = {t["id"] for t in tickets}

    # Merge In Progress from agents/developers and agents/designers (only tickets belonging to this project)
    for type_folder in ("developers", "designers"):
        type_path = AGENTS_WORKSPACE_PATH / type_folder
        if type_path.exists():
            for name_path in sorted(type_path.iterdir()):
                if name_path.is_dir() and not name_path.name.startswith("."):
                    for t in _load_tickets_from_dir(name_path, TicketStatus.IN_PROGRESS):
                        if t.get("project") == project_id and t["id"] not in existing_ids:
                            tickets.append(t)
                            existing_ids.add(t["id"])

    # Merge Verifying from agents/testers (only tickets belonging to this project)
    testers_path = AGENTS_WORKSPACE_PATH / "testers"
    if testers_path.exists():
        for name_path in sorted(testers_path.iterdir()):
            if name_path.is_dir() and not name_path.name.startswith("."):
                for t in _load_tickets_from_dir(name_path, TicketStatus.VERIFYING):
                    if t.get("project") == project_id and t["id"] not in existing_ids:
                        tickets.append(t)
                        existing_ids.add(t["id"])

    return {"name": _display_name(project_id), "project_id": project_id, "tickets": tickets}


def _load_agent(type_folder: str, name_folder: str, tickets_path: Path) -> Agent | None:
    """Load agent from workspace/agents/{type}/{name}/ if it has tickets."""
    tickets = _load_tickets_from_dir(tickets_path, TicketStatus.TODOS)
    if not tickets:
        return None

    position = _TYPE_TO_POSITION.get(type_folder)
    if not position:
        return None

    return {
        "name": name_folder,
        "position": position,
        "ticket": tickets[0],
    }


def refresh() -> None:
    """Load workspace. If projects exist: sync project list (re-scan), update current project's tickets. Otherwise: full load."""
    if not repository.projects:
        # Initial load: projects + agents
        _refresh_full()
        return
    # Hot update: re-scan project list (add/remove), preserve selection, reload current project's tickets only
    current_name = repository.current_project["name"] if repository.current_project else None
    current_project_id = repository.current_project.get("project_id") if repository.current_project else None
    by_id = {p["project_id"]: p for p in repository.projects}
    if WORKSPACE_PATH.exists():
        for project_path in sorted(
            p for p in WORKSPACE_PATH.iterdir() if p.is_dir() and not p.name.startswith(".")
        ):
            pid = project_path.name
            if pid in by_id and pid == current_project_id:
                fresh = _load_project(project_path)
                if fresh:
                    by_id[pid]["tickets"] = fresh["tickets"]
            elif pid not in by_id:
                project = _load_project(project_path)
                if project:
                    by_id[pid] = project
        kept_ids = {project_path.name for project_path in WORKSPACE_PATH.iterdir()
                    if project_path.is_dir() and not project_path.name.startswith(".")}
        for pid in list(by_id):
            if pid not in kept_ids:
                del by_id[pid]
    repository._projects[:] = [by_id[pid] for pid in sorted(by_id)]
    if repository.projects:
        if current_name:
            repository.set_current_by_name(current_name)
        if repository.current_project is None:
            repository.set_current_by_name(repository.projects[0]["name"])


def _refresh_full() -> None:
    """Full load: all projects and agents. Clears repository."""
    repository.clear()
    if WORKSPACE_PATH.exists():
        for project_path in sorted(
            p for p in WORKSPACE_PATH.iterdir() if p.is_dir()
        ):
            project = _load_project(project_path)
            if project:
                repository.projects.append(project)
        if repository.projects:
            repository.set_current_by_name(repository.projects[0]["name"])
    if AGENTS_WORKSPACE_PATH.exists():
        for type_folder in sorted(AGENTS_WORKSPACE_PATH.iterdir()):
            if not type_folder.is_dir() or type_folder.name not in _TYPE_TO_POSITION:
                continue
            for name_path in sorted(type_folder.iterdir()):
                if name_path.is_dir() and not name_path.name.startswith("."):
                    agent = _load_agent(type_folder.name, name_path.name, name_path)
                    if agent:
                        repository.agents.append(agent)
