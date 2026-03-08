from fasthtml.common import *


def Container(*children, **kwargs):
    default_cls = "w-full p-6 mt-8"
    extra_cls = kwargs.pop("cls", "")
    cls = f"{default_cls} {extra_cls}".strip()
    return Div(*children, cls=cls, **kwargs)
