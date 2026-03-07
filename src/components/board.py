from fasthtml.common import *
from typing import List
from config import COLUMNS
from src.components.column import KanbanColumn
from src.models.kanban import Ticket


def KanbanBoard(tickets: List[Ticket]):
    columns = [
        KanbanColumn(col_id, col_info, tickets) for col_id, col_info in COLUMNS.items()
    ]
    return Div(*columns, cls="flex gap-4 overflow-x-auto pb-4 w-full")
