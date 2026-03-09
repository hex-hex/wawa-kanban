from fasthtml.common import *
from src.core.hdrs import get_hdrs
from src.routes.pages import index_page
from src.routes.api import api_kanban, api_ticket, api_ticket_lock, api_ticket_unlock, api_ticket_save, api_ticket_draft, api_project_select, api_refresh, api_refresh_sse

app, rt = fast_app(hdrs=get_hdrs(), pico=False)


@rt("/")
def get():
    return index_page()


@rt("/api/kanban")
def get():
    return api_kanban()


@rt("/api/refresh")
def get():
    return api_refresh()


@rt("/api/refresh-sse")
def get():
    return api_refresh_sse()


@rt("/api/project/select")
def get(project: str):
    return api_project_select(project)


@rt("/api/ticket/{ticket_id}")
def get(ticket_id: str, editable: str = ""):
    return api_ticket(ticket_id, editable)


@rt("/api/ticket/{ticket_id}/lock")
def post(ticket_id: str):
    return api_ticket_lock(ticket_id)


@rt("/api/ticket/{ticket_id}/unlock")
def post(ticket_id: str):
    return api_ticket_unlock(ticket_id)


@rt("/api/ticket/{ticket_id}/save")
def post(ticket_id: str, description: str = ""):
    return api_ticket_save(ticket_id, description)


@rt("/api/ticket/{ticket_id}/draft")
def post(ticket_id: str, description: str = ""):
    return api_ticket_draft(ticket_id, description)


@rt("/api/ticket/{ticket_id}/draft")
def post(ticket_id: str):
    return api_ticket_draft(ticket_id)


if __name__ == "__main__":
    serve(port=5020)
