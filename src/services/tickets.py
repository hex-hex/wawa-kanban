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
    """Load all ticket .md files from a directory."""
    tickets: list[Ticket] = []
    if not dir_path.exists():
        return tickets

    for md_file in sorted(dir_path.glob("*.md")):
        if md_file.stem == "placeholder":
            continue

        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)
        project, mode, _ = _parse_filename(md_file.name)

        tickets.append(
            {
                "id": frontmatter.get("id", md_file.stem),
                "title": frontmatter.get("title", md_file.stem),
                "project": project,
                "description": body,
                "status": status,
                "mode": mode,
            }
        )

    return tickets


def _load_project(project_path: Path) -> Project | None:
    """Load a single project from workspace/projects/{project_id}/."""
    project_id = project_path.name
    if project_id.startswith("."):
        return None

    tickets: list[Ticket] = []
    for status in COLUMNS:
        col_path = project_path / status.value
        tickets.extend(_load_tickets_from_dir(col_path, status))

    return {"name": project_id, "tickets": tickets}


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
