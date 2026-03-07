from fasthtml.common import *


def Title(text: str):
    return H1(text, cls="text-lg font-bold text-gray-100")


def NavBar(title: str, *actions):
    return Div(
        Div(
            Title(title),
            Div(*actions, cls="flex gap-2"),
            cls="flex items-center justify-between w-full max-w-7xl mx-auto",
        ),
        cls="fixed top-0 left-0 right-0 bg-gray-800 px-6 py-3 z-50",
    )


def Container(*children, **kwargs):
    return Div(*children, cls="w-full p-6 mt-16", **kwargs)
