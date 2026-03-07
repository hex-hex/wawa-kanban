from fasthtml.common import Link, Script


def get_hdrs():
    return (
        Link(rel="stylesheet", href="/static/uno.css", type="text/css"),
        Script(src="https://unpkg.com/htmx.org@2"),
    )
