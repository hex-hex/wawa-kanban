import json
from fasthtml.common import *
from src.services.tickets import refresh
from src.models.repository import repository
from src.components.board import KanbanBoard
from src.components.ticket import TicketModal


def _refresh_sse_events():
    """Yield one SSE event with fresh board HTML (no full page reload)."""
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    board = KanbanBoard(tickets)
    html = str(board)
    yield sse_message(json.dumps({"html": html}))


def api_kanban():
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    return KanbanBoard(tickets)


def api_refresh():
    """Load workspace file content and return main content (navbar + board)."""
    from src.routes.pages import _main_content
    return _main_content()


def api_refresh_sse():
    """Stream one SSE event with fresh board HTML for silent in-place update."""
    return EventStream(_refresh_sse_events())


def api_project_select(project: str):
    refresh()
    repository.set_current_by_name(project)
    tickets = (repository.current_project or {}).get("tickets", [])
    return KanbanBoard(tickets)


def api_ticket(ticket_id: str):
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        return Div("Ticket not found", cls="p-8 text-center")

    return TicketModal(ticket)
