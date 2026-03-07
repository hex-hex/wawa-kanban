from fasthtml.common import *


def NavBar(title: str, *actions):
    return Div(
        Div(
            Div(title, cls="text-lg font-bold text-gray-100"),
            Div(*actions, cls="flex gap-2"),
            cls="flex items-center justify-between w-full max-w-7xl mx-auto",
        ),
        cls="fixed top-0 left-0 right-0 bg-gray-800 px-6 py-3 z-50",
    )
