from fasthtml.common import *
from src.services.tickets import refresh
from src.models.repository import PROJECTS
from src.components.board import KanbanBoard
from src.components.ticket import TicketModal


def api_kanban():
    refresh()
    tickets = PROJECTS[0]["tickets"] if PROJECTS else []
    return KanbanBoard(tickets)


def api_ticket(ticket_id: str):
    refresh()
    tickets = PROJECTS[0]["tickets"] if PROJECTS else []
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        return Div("Ticket not found", cls="p-8 text-center")

    return TicketModal(ticket)
