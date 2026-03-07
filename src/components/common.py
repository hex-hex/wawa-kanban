from fasthtml.common import *


def Container(*children, **kwargs):
    return Div(*children, cls="w-full p-6 mt-16", **kwargs)
