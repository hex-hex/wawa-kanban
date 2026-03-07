from pathlib import Path
from src.models.kanban import TicketStatus

WORKSPACE_PATH = Path("workspace/projects")
AGENTS_WORKSPACE_PATH = Path("workspace/agents")

# uno_color: UnoCSS preset color name (gray, blue, amber, violet, emerald)
COLUMNS = {
    TicketStatus.TODOS: {"name": "Todos", "uno_color": "gray"},
    TicketStatus.IN_PROGRESS: {"name": "In Progress", "uno_color": "blue"},
    TicketStatus.WAITING_FOR_VERIFICATION: {
        "name": "Waiting for Verification",
        "uno_color": "amber",
    },
    TicketStatus.VERIFYING: {"name": "Verifying", "uno_color": "violet"},
    TicketStatus.FINISHED: {"name": "Finished", "uno_color": "emerald"},
}

# Explicit order so all columns (incl. Finished) are always rendered
COLUMN_ORDER = [
    TicketStatus.TODOS,
    TicketStatus.IN_PROGRESS,
    TicketStatus.WAITING_FOR_VERIFICATION,
    TicketStatus.VERIFYING,
    TicketStatus.FINISHED,
]

APP_TITLE = "Wawa Kanban"
