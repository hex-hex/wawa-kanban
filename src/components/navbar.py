from fasthtml.common import *


def NavBar(title: str, projects: list, current_project: dict | None, *actions):
    project_options = [
        Option(p["name"], value=p["name"], selected=(p == current_project))
        for p in projects
    ]
    project_select = (
        Span(
            Select(
                *project_options,
                name="project",
                hx_get="/api/project/select",
                hx_include="[name='project']",
                hx_trigger="change",
                hx_target="#kanban-board",
                hx_swap="innerHTML",
                cls="h-8 px-3 py-1.5 text-sm bg-gray-700 text-gray-200 rounded border border-gray-600 focus:border-gray-500 outline-none cursor-pointer box-border flex items-center",
            ),
            cls="flex items-center h-8 shrink-0",
        )
        if projects
        else Span("No projects", cls="text-gray-500 text-sm")
    )

    return Div(
        Div(
            Div(
                Span(cls="i-mdi-view-kanban w-5 h-5 shrink-0 mr-2 text-slate-100"),
                Span(title, cls="text-lg font-bold text-slate-100 py-1 tracking-tight"),
                cls="flex items-center",
            ),
            Div(
                project_select,
                *actions,
                cls="flex items-center gap-2",
            ),
            cls="flex items-center justify-between w-full",
        ),
        cls="sticky top-0 bg-gray-800/95 border-b border-gray-700/80 py-3 z-50 w-full",
    )
