"""E2E tests: HTTP requests against the ASGI app."""

import httpx
from config import COLUMN_ORDER, COLUMNS, APP_TITLE


async def test_index_returns_200_and_all_columns():
    """Homepage returns 200 and HTML contains all kanban column names (incl. Finished)."""
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text
    for col_id in COLUMN_ORDER:
        name = COLUMNS[col_id]["name"]
        assert name in html, f"Column '{name}' must appear on index page"
    assert "Finished" in html, "Finished column must be visible on index page"


async def test_index_contains_app_title_and_kanban_board():
    """Homepage contains app title and main content area."""
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text
    assert APP_TITLE in html
    assert "main-content" in html or "kanban-board" in html


async def test_api_refresh_returns_200_and_all_columns():
    """GET /api/refresh returns 200 and HTML with all columns."""
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/api/refresh")
    assert r.status_code == 200
    html = r.text
    for col_id in COLUMN_ORDER:
        name = COLUMNS[col_id]["name"]
        assert name in html, f"Column '{name}' must appear in refresh response"
    assert "Finished" in html


async def test_navbar_select_and_refresh_alignment():
    """Select and Refresh button must be vertically aligned.
    Regression: container needs flex items-center; both controls need h-8.
    """
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "items-center" in html and "gap-2" in html, (
        "Nav actions container must have items-center and gap-2 for vertical alignment"
    )
    assert "h-8" in html, "Select and Refresh button must have h-8 for consistent height"

    # Verify both controls have h-8: select (or wrapper) and Refresh button
    import re
    has_select_h8 = bool(re.search(r"<select[^>]*\bh-8\b", html))
    has_btn_h8 = bool(re.search(r"<button[^>]*\bh-8\b[^>]*>[\s\S]*?Refresh", html))
    assert has_select_h8, "Project select must have h-8"
    assert has_btn_h8, "Refresh button must have h-8"


async def test_column_headers_have_color_classes():
    """Column headers must use Uno color classes so columns are visually distinct.
    Regression: if color classes are missing from HTML or from uno.css, this fails.
    """
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text
    # Each column uses uno_color from config; header must include the border-{color}-500 class
    for col_id in COLUMN_ORDER:
        uno_color = COLUMNS[col_id]["uno_color"]
        border_class = f"border-{uno_color}-500"
        assert border_class in html, (
            f"Column header for {COLUMNS[col_id]['name']} must have class '{border_class}' (column colors)"
        )


async def test_layout_full_width_no_side_margins():
    """Page must be set up for full-width layout with no left/right whitespace.
    Regression: if someone re-adds max-w-7xl or mx-auto to navbar/main content, this fails.
    """
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text

    assert 'id="wawa-app"' in html or "id='wawa-app'" in html, "Root must have wawa-app for layout preflights"
    assert "main-content" in html, "Main content area must exist"
    assert "kanban-board" in html, "Board container must exist"

    assert "max-w-7xl" not in html, (
        "Layout regression: max-w-7xl must not be used (causes large left/right margins)"
    )
    assert "mx-auto" not in html, (
        "Layout regression: mx-auto must not be used on main content (centers and adds side space)"
    )
