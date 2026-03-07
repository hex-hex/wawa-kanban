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
