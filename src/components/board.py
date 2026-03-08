from fasthtml.common import *
from typing import List
from config import COLUMNS, COLUMN_ORDER
from src.components.column import KanbanColumn
from src.models.kanban import Ticket

def KanbanBoard(tickets: List[Ticket]):
    columns = [
        KanbanColumn(col_id, COLUMNS[col_id], tickets) for col_id in COLUMN_ORDER
    ]
    return Div(
        Div(
            *columns,
            cls="flex flex-col md:flex-row md:flex-nowrap gap-4 pb-4 w-full md:min-w-[calc(5*13rem+4*1rem)]",
        ),
        cls="overflow-x-auto w-full max-w-full",
    )
