from fasthtml.common import *
from config import APP_TITLE
from src.core.hdrs import get_hdrs
from src.services.tickets import refresh
from src.models.repository import repository
from src.components.board import KanbanBoard
from src.components.common import Container
from src.components.navbar import NavBar


def _main_content():
    """Main content fragment: NavBar + KanbanBoard. Calls refresh() to load workspace."""
    refresh()
    current = repository.current_project
    tickets = (current or {}).get("tickets", [])

    return Div(
        NavBar(
            APP_TITLE,
            repository.projects,
            current,
            Button(
                "Refresh",
                hx_get="/api/refresh",
                hx_target="#main-content",
                hx_swap="innerHTML",
                cls="h-8 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-sm transition-colors flex items-center",
            ),
        ),
        Container(
            KanbanBoard(tickets),
            id="kanban-board",
            cls="w-full p-6 mt-8 overflow-x-auto",
            style="overflow-x: auto;",
        ),
        id="main-content",
    )


def index_page():
    return Titled(
        Div(
            _main_content(),
            Div(id="ticket-modal"),
            cls="bg-gray-900 min-h-screen text-gray-100",
        )
    )
