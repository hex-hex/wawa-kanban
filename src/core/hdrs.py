from pathlib import Path

from fasthtml.common import Link, Script, Style
from fastcore.xml import Safe

# Project root (src/core/hdrs.py -> ../../)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_JS_REFRESH_AND_MODAL = _PROJECT_ROOT / "js" / "refresh-and-modal.js"


def _refresh_via_sse_script():
    """Inject client script for refresh, modal, and EasyMDE. Content from js/refresh-and-modal.js."""
    content = _JS_REFRESH_AND_MODAL.read_text(encoding="utf-8")
    return Script(content, type="text/javascript")


_EASYMDE_DARK_CSS = """
.modal-overlay .CodeMirror { background: #1f2937 !important; color: #e5e7eb !important; border-color: #4b5563 !important; }
.modal-overlay .CodeMirror-gutters { background: #111827 !important; border-color: #4b5563 !important; }
.modal-overlay .CodeMirror-cursor { border-left-color: #e5e7eb !important; }
.modal-overlay .CodeMirror-linenumber { color: #6b7280 !important; }
.modal-overlay .CodeMirror-selected { background: #374151 !important; }
.modal-overlay .editor-toolbar { background: #374151 !important; border-color: #4b5563 !important; }
.modal-overlay .editor-toolbar button { color: #d1d5db !important; }
.modal-overlay .editor-toolbar button:hover { background: #4b5563 !important; color: #fff !important; }
.modal-overlay .editor-preview, .modal-overlay .editor-preview-side { background: #1f2937 !important; color: #e5e7eb !important; }
"""


def get_hdrs():
    return (
        Link(rel="stylesheet", href="/static/uno.css", type="text/css"),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.css",
            type="text/css",
        ),
        Style(Safe(_EASYMDE_DARK_CSS)),
        Script(src="https://unpkg.com/htmx.org@2"),
        Script(src="https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.js"),
        _refresh_via_sse_script(),
    )
