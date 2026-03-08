"""Load workspace content (projects, agents) into repository."""

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
from src.services.workspace import parse_frontmatter

# Agent type folder (plural) -> AgentPosition
_TYPE_TO_POSITION: dict[str, AgentPosition] = {
    "testers": AgentPosition.TESTER,
    "designers": AgentPosition.DESIGNER,
    "developers": AgentPosition.DEVELOPER,
}


def _parse_filename(filename: str) -> tuple[str, TaskMode, str]:
    """Parse ticket filename: {project_id}.{phase}.{slug}.md -> (project_id, mode, slug).
    Both formats supported: wawa.proj.default.implementation.setup-project-structure
    and wawa.agent.developer.implementation.fix-login-bug
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
        tickets.append(
            {
                "id": tid,
                "title": frontmatter.get("title", Path(parse_name).stem),
                "project": project,
                "description": body,
                "status": status,
                "mode": mode,
                "locked": locked,
            }
        )

    for lock_file in sorted(dir_path.glob("*.md.lock")):
        load_file(lock_file, lock_file.name.removesuffix(".lock"), locked=True)

    for md_file in sorted(dir_path.glob("*.md")):
        load_file(md_file, md_file.name, locked=False)

    return tickets


PROJECT_NAME_PREFIX = "wawa.proj."


def _find_ticket_file(ticket_id: str) -> Path | None:
    """Find the .md or .md.lock file for a ticket by id (from frontmatter)."""
    if not WORKSPACE_PATH.exists():
        return None
    for project_path in sorted(WORKSPACE_PATH.iterdir()):
        if not project_path.is_dir() or project_path.name.startswith("."):
            continue
        for status in COLUMNS:
            col_path = project_path / status.value
            if not col_path.exists():
                continue
            for pattern in ["*.md", "*.md.lock"]:
                for f in sorted(col_path.glob(pattern)):
                    if "placeholder" in f.name:
                        continue
                    try:
                        content = f.read_text()
                        frontmatter, _ = parse_frontmatter(content)
                        if frontmatter.get("id") == ticket_id:
                            return f
                    except OSError:
                        continue
    return None


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


def _display_name(project_id: str) -> str:
    """Return project name for UI: strip prefix 'wawa.proj.' if present."""
    if project_id.startswith(PROJECT_NAME_PREFIX):
        return project_id[len(PROJECT_NAME_PREFIX) :]
    return project_id


def _load_project(project_path: Path) -> Project | None:
    """Load a single project from workspace/projects/{project_id}/."""
    project_id = project_path.name
    if project_id.startswith("."):
        return None

    tickets: list[Ticket] = []
    for status in COLUMNS:
        col_path = project_path / status.value
        tickets.extend(_load_tickets_from_dir(col_path, status))

    return {"name": _display_name(project_id), "tickets": tickets}


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
    """Load workspace content into repository. Preserves current project selection (hot update)."""
    current_name = (
        repository.current_project["name"] if repository.current_project else None
    )
    repository.clear()

    # Load projects: workspace/projects/{project_id}/{status}/*.md
    if WORKSPACE_PATH.exists():
        project_dirs = sorted(
            p for p in WORKSPACE_PATH.iterdir() if p.is_dir()
        )
        for project_path in project_dirs:
            project = _load_project(project_path)
            if project:
                repository.projects.append(project)
        # Restore selection: same project by name, or first if none was selected
        if repository.projects:
            if current_name:
                repository.set_current_by_name(current_name)
            if repository.current_project is None:
                repository.set_current_by_name(repository.projects[0]["name"])

    # Load agents: workspace/agents/{type}/{name}/*.md
    # Rule: type folder (testers/designers/developers) -> name folder (default, ...)
    if AGENTS_WORKSPACE_PATH.exists():
        for type_folder in sorted(AGENTS_WORKSPACE_PATH.iterdir()):
            if not type_folder.is_dir() or type_folder.name not in _TYPE_TO_POSITION:
                continue

            for name_path in sorted(type_folder.iterdir()):
                if name_path.is_dir() and not name_path.name.startswith("."):
                    agent = _load_agent(
                        type_folder.name, name_path.name, name_path
                    )
                    if agent:
                        repository.agents.append(agent)
