from fasthtml.common import *
from typing import List
from config import COLUMNS
from src.components.ticket import TicketCard


def KanbanColumn(col_id: str, col_info: dict, tickets: List[dict]):
    col_tickets = [t for t in tickets if t["column"] == col_id]
    cards = [TicketCard(t) for t in col_tickets]

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
            *cards
            if cards
            else [Div("No tickets", cls="text-gray-500 text-sm p-4 text-center")],
            cls="p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-200px)]",
        ),
        cls="flex flex-col min-w-72 w-72 bg-gray-800 rounded-lg",
    )


def KanbanBoard(tickets: List[dict]):
    columns = [
        KanbanColumn(col_id, col_info, tickets) for col_id, col_info in COLUMNS.items()
    ]
    return Div(*columns, cls="flex gap-4 overflow-x-auto pb-4 w-full")
