from fasthtml.common import *
from config import APP_TITLE
from src.core.hdrs import get_hdrs
from src.services.tickets import refresh
from src.models.repository import repository
from src.components.board import KanbanBoard
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
                Span(cls="i-mdi-refresh w-4 h-4 shrink-0 mr-2 text-gray-200"),
                "Refresh",
                id="btn-refresh",
                type="button",
                cls="h-10 min-h-[44px] md:h-8 md:min-h-0 px-3 py-2 md:py-1.5 bg-gray-700 text-gray-200 rounded-lg border border-gray-600 hover:bg-gray-600 hover:border-gray-500 text-sm transition-colors flex items-center shrink-0 outline-none cursor-pointer",
            ),
        ),
        Div(
            KanbanBoard(tickets),
            id="kanban-board",
            cls="w-full overflow-x-auto mt-4 min-w-0 px-4 md:px-0 box-border",
        ),
        id="main-content",
        cls="w-full",
    )


def index_page():
    return (
        Title(APP_TITLE),
        Div(
            _main_content(),
            Div(id="ticket-modal"),
            id="wawa-app",
            cls="bg-gray-950 min-h-screen text-gray-100",
        ),
    )
