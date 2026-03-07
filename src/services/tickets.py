from pathlib import Path
from config import WORKSPACE_PATH, AGENTS_WORKSPACE_PATH, CURRENT_PROJECT, COLUMNS
from src.models.kanban import (
    Ticket,
    TicketStatus,
    TaskMode,
    Project,
    Agent,
    AgentPosition,
)
from src.models.repository import PROJECTS, AGENTS
from src.services.workspace import parse_frontmatter


def _parse_filename(filename: str) -> tuple[str, TaskMode, str]:
    parts = filename.replace(".md", "").split(".")
    project = parts[0] if len(parts) > 0 else ""
    mode = TaskMode(parts[1]) if len(parts) > 1 else TaskMode.IMPLEMENTATION
    title = ".".join(parts[2:]) if len(parts) > 2 else ""
    return project, mode, title


def _load_tickets_from_dir(dir_path: Path, status: TicketStatus) -> list[Ticket]:
    tickets = []
    if not dir_path.exists():
        return tickets

    for md_file in dir_path.glob("*.md"):
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


def refresh():
    PROJECTS.clear()
    AGENTS.clear()

    project_tickets: list[Ticket] = []
    for status in COLUMNS.keys():
        col_path = WORKSPACE_PATH / CURRENT_PROJECT / status.value
        project_tickets.extend(_load_tickets_from_dir(col_path, status))

    PROJECTS.append(
        {
            "name": CURRENT_PROJECT,
            "tickets": project_tickets,
        }
    )

    for agent_pos in AgentPosition:
        agent_path = AGENTS_WORKSPACE_PATH / agent_pos.value
        tickets = _load_tickets_from_dir(agent_path, TicketStatus.TODOS)

        if tickets:
            AGENTS.append(
                {
                    "name": agent_pos.value,
                    "position": agent_pos,
                    "ticket": tickets[0],
                }
            )
