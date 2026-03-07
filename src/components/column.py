from fasthtml.common import *
from typing import List
from src.models.kanban import Ticket, TicketStatus
from config import COLUMNS


def KanbanColumn(col_id: TicketStatus, col_info: dict, tickets: List[Ticket]):
    col_tickets = [t for t in tickets if t["status"] == col_id]

    return Div(
        Div(
            Div(
                Span(
                    cls=f"i-{col_info['icon']} w-4 h-4 shrink-0 mr-2 text-{col_info['uno_color']}-400",
                ),
                Span(
                    col_info["name"],
                    cls=f"text-sm font-semibold text-{col_info['uno_color']}-400 whitespace-nowrap",
                ),
                Span(
                    str(len(col_tickets)),
                    cls=f"ml-2 bg-{col_info['uno_color']}-500/50 text-white text-xs px-2 py-0.5 rounded-full font-medium",
                ),
                cls="flex items-center",
            ),
            cls=f"px-6 py-3 rounded-t-lg bg-{col_info['uno_color']}-500/20 border-b-3 border-{col_info['uno_color']}-500",
        ),
        Div(
            *[ticket_to_card(t) for t in col_tickets]
            if col_tickets
            else [Div("No tickets", cls="text-gray-500 text-sm p-4 text-center")],
            cls="p-3 space-y-3 overflow-y-auto max-h-[calc(100vh-200px)] min-h-[120px] flex-1",
        ),
        cls="flex flex-col min-w-52 flex-1 bg-gray-800/80 rounded-lg border border-gray-700/50",
    )


def ticket_to_card(ticket: Ticket):
    from src.components.ticket import TicketCard

    return TicketCard(ticket)
