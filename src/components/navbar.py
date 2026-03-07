from fasthtml.common import *


def NavBar(title: str, projects: list, current_project: dict | None, *actions):
    project_options = [
        Option(p["name"], value=p["name"], selected=(p == current_project))
        for p in projects
    ]
    project_select = Select(
        *project_options,
        name="project",
        hx_get="/api/project/select",
        hx_include="[name='project']",
        hx_trigger="change",
        hx_target="#kanban-board",
        hx_swap="innerHTML",
        cls="h-8 bg-gray-700 text-gray-200 rounded px-3 py-1.5 text-sm border border-gray-600 focus:border-gray-500 outline-none leading-none cursor-pointer",
    ) if projects else Span("No projects", cls="text-gray-500 text-sm")

    return Div(
        Div(
            Div(title, cls="text-lg font-bold text-gray-100 py-1"),
            Div(
                project_select,
                *actions,
                cls="flex items-center gap-2",
            ),
            cls="flex items-center justify-between w-full max-w-7xl mx-auto px-4",
        ),
        cls="sticky top-0 bg-gray-800 px-6 py-3 z-50",
    )
