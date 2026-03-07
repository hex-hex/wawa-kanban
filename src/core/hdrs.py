from fasthtml.common import Link, Script


def get_hdrs():
    return (
        Link(rel="stylesheet", href="/static/uno.css", type="text/css"),
        Link(rel="stylesheet", href="/static/kanban.css", type="text/css"),
        Script(src="https://unpkg.com/htmx.org@2"),
    )
