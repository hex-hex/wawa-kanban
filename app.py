from fasthtml.common import *
from pathlib import Path

app, rt = fast_app(
    hdrs=(
        Link(rel="stylesheet", href="/static/uno.css", type="text/css"),
        Script(src="https://unpkg.com/htmx.org@2"),
    )
)

WORKSPACE_PATH = Path("workspace/projects/wawa_proj_default")

COLUMNS = {
    "backlog": {"name": "Backlog", "color": "#6B7280"},
    "implementing": {"name": "Implementing", "color": "#3B82F6"},
    "verifying": {"name": "Verifying", "color": "#F59E0B"},
    "finished": {"name": "Finished", "color": "#10B981"},
}

PRIORITY_COLORS = {
    "high": "#EF4444",
    "medium": "#F59E0B",
    "low": "#9CA3AF",
}


def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    frontmatter = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    body = parts[2].strip() if len(parts) > 2 else ""
    return frontmatter, body


def get_tickets():
    tickets = []
    for col_id in COLUMNS:
        col_path = WORKSPACE_PATH / col_id
        if not col_path.exists():
            continue

        for md_file in col_path.glob("*.md"):
            content = md_file.read_text()
            frontmatter, body = parse_frontmatter(content)

            ticket_id = frontmatter.get("id", md_file.stem)
            tickets.append(
                {
                    "id": ticket_id,
                    "title": frontmatter.get("title", md_file.stem),
                    "priority": frontmatter.get("priority", "medium"),
                    "created": frontmatter.get("created", ""),
                    "column": col_id,
                    "body": body,
                    "filename": md_file.name,
                }
            )

    return tickets


def ticket_card(ticket):
    return Div(
        Div(
            Span(ticket["id"], cls="text-xs font-mono text-gray-500"),
            cls="flex justify-between items-center mb-2",
        ),
        Div(ticket["title"], cls="font-semibold text-sm mb-2 line-clamp-2"),
        Div(ticket["created"], cls="text-xs text-gray-400"),
        cls=(
            "bg-white rounded-lg p-3 shadow-sm border border-gray-200 "
            "hover:shadow-md hover:-translate-y-0.5 cursor-pointer transition-all duration-200"
        ),
        hx_get=f"/api/ticket/{ticket['id']}",
        hx_target="#ticket-modal",
        hx_swap="innerHTML",
    )


def kanban_column(col_id, col_info, tickets):
    col_tickets = [t for t in tickets if t["column"] == col_id]
    cards = [ticket_card(t) for t in col_tickets]

    return Div(
        Div(
            Div(
                Span(col_info["name"], cls="font-semibold"),
                Span(
                    str(len(col_tickets)),
                    cls="ml-2 bg-gray-200 text-gray-700 text-xs px-2 py-0.5 rounded-full",
                ),
                cls="flex items-center",
            ),
            cls="px-4 py-3 rounded-t-lg",
            style=f"background-color: {col_info['color']}20; border-bottom: 3px solid {col_info['color']}",
        ),
        Div(
            *cards
            if cards
            else [Div("No tickets", cls="text-gray-400 text-sm p-4 text-center")],
            cls="p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-200px)]",
        ),
        cls="flex flex-col min-w-72 w-72 bg-gray-50 rounded-lg",
    )


@rt("/")
def index():
    tickets = get_tickets()
    columns = [
        kanban_column(col_id, col_info, tickets) for col_id, col_info in COLUMNS.items()
    ]

    return Titled(
        "Wawa Kanban",
        Div(
            Div(
                H1("Wawa Kanban", cls="text-xl font-bold"),
                Button(
                    "Refresh",
                    hx_get="/api/kanban",
                    hx_target="#kanban-board",
                    hx_swap="innerHTML",
                    cls="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors",
                ),
                cls="flex justify-between items-center mb-6",
            ),
            Div(*columns, id="kanban-board", cls="flex gap-4 overflow-x-auto pb-4"),
            cls="max-w-7xl mx-auto p-6",
        ),
        Div(id="ticket-modal"),
        cls="bg-gray-100 min-h-screen",
    )


@rt("/api/kanban")
def api_kanban():
    tickets = get_tickets()
    columns = [
        kanban_column(col_id, col_info, tickets) for col_id, col_info in COLUMNS.items()
    ]
    return Div(*columns, cls="flex gap-4 overflow-x-auto pb-4")


@rt("/api/ticket/{ticket_id}")
def api_ticket(ticket_id: str):
    tickets = get_tickets()
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        return Div("Ticket not found", cls="p-8 text-center")

    priority_color = PRIORITY_COLORS.get(ticket["priority"], "#9CA3AF")

    return Div(
        Div(
            Div(
                H2(ticket["title"], cls="text-xl font-bold mb-4"),
                Div(
                    Span(
                        ticket["priority"].upper(),
                        cls="px-2 py-0.5 rounded text-xs font-medium",
                        style=f"background-color: {priority_color}20; color: {priority_color}",
                    ),
                    Span(ticket["id"], cls="ml-2 font-mono text-sm text-gray-500"),
                    cls="flex items-center gap-2 mb-4",
                ),
                Div("Created: " + ticket["created"], cls="text-sm text-gray-600 mb-4"),
                Hr(cls="my-4"),
                Div(
                    ticket["body"] or "No description",
                    cls="text-gray-700 whitespace-pre-wrap",
                ),
                cls="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto",
            ),
            cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
            onclick="if(event.target === this) this.remove()",
        ),
        onclick="if(event.target.id === 'ticket-modal') this.remove()",
        id="ticket-modal",
        cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
    )


serve(port=5020)
