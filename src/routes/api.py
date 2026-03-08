import json
from fasthtml.common import *
from src.services.tickets import refresh, lock_ticket, unlock_ticket, save_ticket_body
from src.models.repository import repository
from src.components.board import KanbanBoard
from src.components.ticket import TicketModal


def _refresh_sse_events():
    """Yield one SSE event with fresh board HTML and existing ticket IDs (by frontmatter id)."""
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    board = KanbanBoard(tickets)
    html = str(board)
    existing_ids = [t["id"] for t in tickets]
    yield sse_message(json.dumps({"html": html, "existing_ids": existing_ids}))


def api_kanban():
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    return KanbanBoard(tickets)


def api_refresh():
    """Load workspace file content and return main content (navbar + board)."""
    from src.routes.pages import _main_content
    return _main_content()


def api_refresh_sse():
    """Stream one SSE event with fresh board HTML for silent in-place update."""
    return EventStream(_refresh_sse_events())


def api_project_select(project: str):
    refresh()
    repository.set_current_by_name(project)
    tickets = (repository.current_project or {}).get("tickets", [])
    return KanbanBoard(tickets)


def api_ticket(ticket_id: str, editable: str = ""):
    refresh()
    tickets = (repository.current_project or {}).get("tickets", [])
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        return Div("Ticket not found", cls="p-8 text-center")

    show_edit_mode = editable.lower() in ("1", "true", "yes")
    return TicketModal(ticket, editable=show_edit_mode)


def api_ticket_lock(ticket_id: str):
    """Lock ticket: rename .md to .md.lock."""
    ok = lock_ticket(ticket_id)
    if not ok:
        return Response(status_code=404, content="Ticket not found or already locked")
    return Response(status_code=200, content="", headers={"HX-Trigger": "refreshBoard"})


def api_ticket_unlock(ticket_id: str):
    """Unlock ticket: rename .md.lock back to .md."""
    ok = unlock_ticket(ticket_id)
    if not ok:
        return Response(status_code=404, content="Ticket not found or already unlocked")
    return Response(
        status_code=200,
        content="",
        headers={"HX-Trigger": json.dumps({"refreshBoard": {"closeModal": True}})},
    )


def _ticket_save_response(close_modal: bool = True):
    """HX-Trigger to refresh board and optionally close modal."""
    payload = json.dumps({"refreshBoard": {"closeModal": close_modal}})
    return Response(status_code=200, content="", headers={"HX-Trigger": payload})


def api_ticket_save(ticket_id: str, description: str = ""):
    """Confirm: save editor content to .lock file, rename to .md (unlock), dismiss modal."""
    if not save_ticket_body(ticket_id, description):
        return Response(status_code=404, content="Ticket not found or not locked")
    if not unlock_ticket(ticket_id):
        return Response(status_code=500, content="Failed to unlock")
    return _ticket_save_response(close_modal=True)


def api_ticket_draft(ticket_id: str, description: str = ""):
    """Save Draft: save editor content to .lock file, dismiss modal (stay locked)."""
    if not save_ticket_body(ticket_id, description):
        return Response(status_code=404, content="Ticket not found or not locked")
    return _ticket_save_response(close_modal=True)
