from fasthtml.common import *


def Container(*children, **kwargs):
    return Div(*children, cls="max-w-7xl mx-auto p-6", **kwargs)


def PageHeader(title: str, *actions):
    return Div(
        H1(title, cls="text-xl font-bold"),
        Div(*actions, cls="flex gap-2"),
        cls="flex justify-between items-center mb-6",
    )
