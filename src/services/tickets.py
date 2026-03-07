from pathlib import Path
from typing import List
from config import WORKSPACE_PATH, COLUMNS
from src.models.kanban import Ticket
from src.services.workspace import parse_frontmatter


def get_tickets() -> List[Ticket]:
    tickets = []
    for col_id in COLUMNS:
        col_path = WORKSPACE_PATH / col_id
        if not col_path.exists():
            continue

        for md_file in col_path.glob("*.md"):
            if md_file.name == "placeholder":
                continue

            content = md_file.read_text()
            frontmatter, body = parse_frontmatter(content)

            ticket_id = frontmatter.get("id", md_file.stem)
            tickets.append(
                {
                    "id": ticket_id,
                    "title": frontmatter.get("title", md_file.stem),
                    "priority": frontmatter.get("priority", "medium"),
                    "created": frontmatter.get("created", ""),
                    "column": col_id,
                    "body": body,
                    "filename": md_file.name,
                }
            )

    return tickets
