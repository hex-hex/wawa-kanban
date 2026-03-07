from fasthtml.common import *
from config import APP_TITLE
from src.core.hdrs import get_hdrs
from src.services.tickets import get_tickets
from src.components.board import KanbanBoard
from src.components.common import Container, PageHeader


def index_page():
    tickets = get_tickets()

    return Titled(
        APP_TITLE,
        Container(
            PageHeader(
                APP_TITLE,
                Button(
                    "Refresh",
                    hx_get="/api/kanban",
                    hx_target="#kanban-board",
                    hx_swap="innerHTML",
                    cls="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors",
                ),
            ),
            KanbanBoard(tickets),
        ),
        Div(id="ticket-modal"),
        cls="bg-gray-100 min-h-screen",
    )
