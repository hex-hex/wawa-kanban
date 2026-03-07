from pathlib import Path
from src.models.kanban import TicketStatus

WORKSPACE_PATH = Path("workspace/projects")
AGENTS_WORKSPACE_PATH = Path("workspace/agents")

COLUMNS = {
    TicketStatus.TODOS: {"name": "Todos", "color": "#6B7280"},
    TicketStatus.IN_PROGRESS: {"name": "In Progress", "color": "#3B82F6"},
    TicketStatus.WAITING_FOR_VERIFICATION: {
        "name": "Waiting for Verification",
        "color": "#F59E0B",
    },
    TicketStatus.VERIFYING: {"name": "Verifying", "color": "#8B5CF6"},
    TicketStatus.FINISHED: {"name": "Finished", "color": "#10B981"},
}

APP_TITLE = "Wawa Kanban"
