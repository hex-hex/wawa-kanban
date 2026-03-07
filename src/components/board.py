from fasthtml.common import *
from typing import List
from config import COLUMNS, COLUMN_ORDER
from src.components.column import KanbanColumn
from src.models.kanban import Ticket

# 5 columns × 13rem + 4 gaps × 1rem — narrow enough that 5 columns (incl. Finished) often fit one screen
BOARD_MIN_WIDTH_CSS = "calc(5 * 13rem + 4 * 1rem)"


def KanbanBoard(tickets: List[Ticket]):
    columns = [
        KanbanColumn(col_id, COLUMNS[col_id], tickets) for col_id in COLUMN_ORDER
    ]
    return Div(
        Div(
            *columns,
            cls="flex flex-nowrap gap-4 pb-4",
            style=f"min-width: {BOARD_MIN_WIDTH_CSS}; width: max-content; display: flex; flex-wrap: nowrap;",
        ),
        style="overflow-x: auto; overflow-y: visible; width: 100%; max-width: 100%;",
    )
