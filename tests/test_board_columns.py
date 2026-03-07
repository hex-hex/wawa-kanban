"""Ensure all kanban columns (incl. Finished) are rendered in the board."""

import pytest
from config import COLUMN_ORDER, COLUMNS
from src.components.board import KanbanBoard


def test_all_columns_display_in_kanban_board():
    """All columns from COLUMN_ORDER must appear in the rendered board HTML."""
    board = KanbanBoard(tickets=[])
    html = str(board)

    column_names = [COLUMNS[col_id]["name"] for col_id in COLUMN_ORDER]
    for name in column_names:
        assert name in html, f"Column '{name}' should appear in board HTML"

    assert len(column_names) == 5, "There must be exactly 5 columns (incl. Finished)"


def test_finished_column_specifically_displayed():
    """Finished column must be present so it is never missing from the UI."""
    board = KanbanBoard(tickets=[])
    html = str(board)
    assert "Finished" in html, "Finished column must be visible in the board"
