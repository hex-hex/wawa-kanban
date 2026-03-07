from fasthtml.common import *
from src.core.hdrs import get_hdrs
from src.routes.pages import index_page
from src.routes.api import api_kanban, api_ticket

app, rt = fast_app(hdrs=get_hdrs())


@rt("/")
def get():
    return index_page()


@rt("/api/kanban")
def get():
    return api_kanban()


@rt("/api/ticket/{ticket_id}")
def get(ticket_id: str):
    return api_ticket(ticket_id)


serve(port=5020)
