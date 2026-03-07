from fasthtml.common import *
from config import APP_TITLE
from src.core.hdrs import get_hdrs
from src.services.tickets import refresh
from src.models.repository import PROJECTS
from src.components.board import KanbanBoard
from src.components.common import Container
from src.components.navbar import NavBar


def index_page():
    refresh()
    tickets = PROJECTS[0]["tickets"] if PROJECTS else []

    return Titled(
        Div(
            NavBar(
                APP_TITLE,
                Button(
                    "Refresh",
                    hx_get="/api/kanban",
                    hx_target="#kanban-board",
                    hx_swap="innerHTML",
                    cls="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-sm transition-colors",
                ),
            ),
            Container(KanbanBoard(tickets)),
        ),
        Div(id="ticket-modal"),
        cls="bg-gray-900 min-h-screen text-gray-100",
    )
