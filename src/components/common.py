from fasthtml.common import *


def CardBodyScroll(*children, **kwargs):
    """Scrollable area for long card content (e.g. markdown). Use inside a flex-col container with max-h.
    Gives vertical scrollbar when content overflows. Base card feature for all subclasses."""
    return Div(
        *children,
        cls="flex-1 min-h-0 overflow-y-auto",
        **kwargs,
    )


def CardCloseButton(label="Close", onclick=None, **kwargs):
    """Unified Close button for all cards/modals. Pass onclick for modal dismiss script.
    Keep cls as a literal string so build-css.mjs extractor can pick up the classes."""
    return Button(
        label,
        type="button",
        aria_label="Close",
        cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-gray-700 text-gray-300 hover:text-gray-100 hover:bg-gray-600 rounded transition-colors outline-none cursor-pointer",
        onclick=onclick,
        **kwargs,
    )


def Container(*children, **kwargs):
    default_cls = "w-full p-6 mt-8"
    extra_cls = kwargs.pop("cls", "")
    cls = f"{default_cls} {extra_cls}".strip()
    return Div(*children, cls=cls, **kwargs)
