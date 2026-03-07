from fasthtml.common import *
from src.services.tickets import refresh
from src.models.repository import repository
from src.components.board import KanbanBoard
from src.components.ticket import TicketModal


def api_kanban():
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    return KanbanBoard(tickets)


def api_refresh():
    """Load workspace file content and return main content (navbar + board)."""
    from src.routes.pages import _main_content
    return _main_content()


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
