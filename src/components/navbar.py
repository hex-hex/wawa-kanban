from fasthtml.common import *


def NavBar(title: str, projects: list, current_project: dict | None, *actions):
    project_options = [
        Option(p["name"], value=p["name"], selected=(p == current_project))
        for p in projects
    ]
    project_select = (
        Div(
            Select(
                *project_options,
                name="project",
                hx_get="/api/project/select",
                hx_include="[name='project']",
                hx_trigger="change",
                hx_target="#main-content",
                hx_swap="outerHTML",
                cls="h-10 md:h-8 min-h-[44px] md:min-h-0 w-full max-w-full min-w-0 md:w-auto md:min-w-44 px-3 py-2 md:py-1.5 text-sm bg-gray-700 text-gray-200 rounded-lg border border-gray-600 focus:border-gray-500 focus:ring-2 focus:ring-gray-500/30 outline-none cursor-pointer box-border",
            ),
            cls="w-full min-w-0 max-w-full overflow-hidden md:w-auto md:max-w-none md:overflow-visible",
        )
        if projects
        else Div("No projects", cls="text-gray-500 text-sm")
    )

    return Div(
        Div(
            Div(
                Span(cls="i-mdi-view-kanban w-5 h-5 shrink-0 mr-2 text-slate-100"),
                Span(title, cls="text-lg font-bold text-slate-100 py-1 tracking-tight"),
                Div(*actions, cls="flex items-center gap-2 shrink-0 min-h-[44px] md:min-h-0 items-center"),
                cls="flex items-center gap-2 md:gap-4 shrink-0",
            ),
            Div(project_select, cls="flex items-center justify-center min-w-0 w-full md:w-auto overflow-hidden pr-4 md:pr-0"),
            Div(cls="hidden md:block shrink-0"),
            cls="flex flex-col md:grid md:grid-cols-[1fr_auto_1fr] items-stretch md:items-center gap-3 md:gap-2 w-full min-w-0",
        ),
        id="navbar",
        cls="sticky top-0 bg-gray-800/95 border-b border-gray-700/80 py-3 px-4 md:pl-4 md:pr-8 z-50 w-full max-w-full min-w-0 overflow-hidden box-border",
    )
