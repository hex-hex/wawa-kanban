from pathlib import Path
from src.models.kanban import TicketStatus

WORKSPACE_PATH = Path("workspace/projects")
AGENTS_WORKSPACE_PATH = Path("workspace/agents")

# uno_color: UnoCSS preset color; icon: mdi icon class (e.g. mdi-checkbox-blank-outline)
COLUMNS = {
    TicketStatus.TODOS: {"name": "Todos", "uno_color": "gray", "icon": "mdi-checkbox-blank-outline"},
    TicketStatus.IN_PROGRESS: {"name": "In Progress", "uno_color": "blue", "icon": "mdi-progress-clock"},
    TicketStatus.WAITING_FOR_VERIFICATION: {
        "name": "Waiting for Verification",
        "uno_color": "amber",
        "icon": "mdi-clock-outline",
    },
    TicketStatus.VERIFYING: {"name": "Verifying", "uno_color": "violet", "icon": "mdi-check-circle-outline"},
    TicketStatus.FINISHED: {"name": "Finished", "uno_color": "emerald", "icon": "mdi-check-circle"},
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
