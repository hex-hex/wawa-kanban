from fasthtml.common import *
from typing import List
from src.models.kanban import Ticket, TicketStatus
from config import COLUMNS


def KanbanColumn(col_id: TicketStatus, col_info: dict, tickets: List[Ticket]):
    col_tickets = [t for t in tickets if t["status"] == col_id]

    return Div(
        Div(
            Div(
                Span(col_info["name"], cls="text-sm font-semibold"),
                Span(
                    str(len(col_tickets)),
                    cls="ml-2 bg-gray-600 text-gray-200 text-xs px-2 py-0.5 rounded-full",
                ),
                cls="flex items-center",
            ),
            cls="px-4 py-3 rounded-t-lg",
            style=f"background-color: {col_info['color']}20; border-bottom: 3px solid {col_info['color']}",
        ),
        Div(
            *[ticket_to_card(t) for t in col_tickets]
            if col_tickets
            else [Div("No tickets", cls="text-gray-500 text-sm p-4 text-center")],
            cls="p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-200px)] min-h-[120px] flex-1",
        ),
        cls="flex flex-col min-w-52 w-52 flex-shrink-0 bg-gray-800 rounded-lg",
    )


def ticket_to_card(ticket: Ticket):
    from src.components.ticket import TicketCard

    return TicketCard(ticket)
