from fasthtml.common import *
from src.services.tickets import get_tickets
from src.components.board import KanbanBoard
from src.components.ticket import TicketModal


def api_kanban():
    tickets = get_tickets()
    return KanbanBoard(tickets)


def api_ticket(ticket_id: str):
    tickets = get_tickets()
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        return Div("Ticket not found", cls="p-8 text-center")

    return TicketModal(ticket)
