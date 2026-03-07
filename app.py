from fasthtml.common import *
from src.core.hdrs import get_hdrs
from src.routes.pages import index_page
from src.routes.api import api_kanban, api_ticket, api_project_select, api_refresh

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


@rt("/api/project/select")
def get(project: str):
    return api_project_select(project)


@rt("/api/ticket/{ticket_id}")
def get(ticket_id: str):
    return api_ticket(ticket_id)


if __name__ == "__main__":
    serve(port=5020)
