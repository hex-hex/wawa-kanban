"""Markdown to HTML conversion for safe rendering in FastHTML."""

import markdown
from fastcore.xml import Safe


def md_to_safe_html(text: str | None) -> Safe:
    """Convert markdown text to HTML, wrapped in Safe for unescaped rendering."""
    if not text or not text.strip():
        return Safe("")
    html = markdown.markdown(text, extensions=["nl2br"])
    return Safe(html)
