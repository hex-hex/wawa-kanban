"""E2E tests: repeatedly open and close the ticket modal (server and browser)."""

import os
import re
import socket
import subprocess
import threading
import time
from pathlib import Path

import httpx
import pytest

# Port for the browser test server
MODAL_TEST_PORT = 5021

# Project-local browser dir: one version, no pollution of system cache
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PLAYWRIGHT_BROWSERS_PATH = _PROJECT_ROOT / ".playwright-browsers"


def _wait_for_port(port: int, timeout: float = 10.0) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    return False


# ----- HTTP-only test (no browser) -----


async def test_modal_content_returned_20_times():
    """Request ticket modal HTML 20 times; each response must be 200 with modal content."""
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text
    match = re.search(r'hx-get=["\']/?api/ticket/([^"\']+)["\']', html)
    assert match, "Page must contain at least one ticket card with hx-get to /api/ticket/{id}"
    ticket_id = match.group(1).strip("/")
    assert ticket_id

    n = 20
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for i in range(n):
            r = await client.get(f"/api/ticket/{ticket_id}")
            assert r.status_code == 200, f"iteration {i + 1}/{n}"
            body = r.text
            assert "modal-overlay" in body, f"iteration {i + 1}/{n}"
            assert 'aria-label="Close"' in body or "aria-label='Close'" in body, f"iteration {i + 1}/{n}"


async def test_todos_column_editable_modal_and_other_columns_plain_modal():
    """Todos column cards request modal with editable=1 (Edit Mode button); other columns do not.
    API: without editable param -> modal has Close only; with editable=1 -> modal has Edit Mode and Close.
    """
    from app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/")
    assert r.status_code == 200
    html = r.text

    # Page must contain at least one Todos card (editable=1) and one non-Todos card (no editable)
    has_editable_card = "editable=1" in html and "api/ticket/" in html
    assert has_editable_card, "Page must contain at least one ticket card with hx-get to /api/ticket/{id}?editable=1 (Todos column)"

    # Get any ticket id from a card (e.g. first match without editable)
    match = re.search(r'hx-get=["\']/?api/ticket/([^"?\'&\s]+)', html)
    assert match, "Page must contain at least one ticket card with hx-get to /api/ticket/{id}"
    ticket_id = match.group(1).strip("/")
    assert ticket_id

    # Without editable: modal has Close, no Edit Mode button
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get(f"/api/ticket/{ticket_id}")
    assert r.status_code == 200
    body = r.text
    assert "modal-overlay" in body
    assert "Close" in body
    assert "Edit Mode" not in body

    # With editable=1: modal has both Edit Mode and Close
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get(f"/api/ticket/{ticket_id}", params={"editable": "1"})
    assert r.status_code == 200
    body = r.text
    assert "modal-overlay" in body
    assert "Close" in body
    assert "Edit Mode" in body


# ----- Browser test: open and close modal 20 times -----


def _ensure_playwright_chromium():
    """Use project-local browser dir; install chromium if missing (single version)."""
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(_PLAYWRIGHT_BROWSERS_PATH)}
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_PLAYWRIGHT_BROWSERS_PATH)
    subprocess.run(
        ["uv", "run", "playwright", "install", "chromium"],
        cwd=_PROJECT_ROOT,
        env=env,
        capture_output=True,
        check=False,
    )


@pytest.fixture(scope="module")
def app_server():
    """Start the ASGI app for the browser test."""
    import uvicorn
    from app import app

    def run():
        uvicorn.run(app, host="127.0.0.1", port=MODAL_TEST_PORT, log_level="warning")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    if not _wait_for_port(MODAL_TEST_PORT):
        raise RuntimeError(f"Server did not start on port {MODAL_TEST_PORT}")
    yield f"http://127.0.0.1:{MODAL_TEST_PORT}"


@pytest.mark.asyncio
async def test_modal_opens_and_closes_20_times_in_browser(app_server):
    """In a real browser: open modal (click card), close (click Close), repeat 20 times.
    Each time the modal must open. Catches regression where rapid open/close breaks opening.
    Chromium is installed to .playwright-browsers/ (one version, project-managed) if missing.
    """
    _ensure_playwright_chromium()
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_PLAYWRIGHT_BROWSERS_PATH)

    from playwright.async_api import async_playwright

    base_url = app_server
    n = 20

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as e:
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                pytest.skip(
                    "Chromium not available after install. Try: uv sync --extra test && uv run playwright install chromium"
                )
            raise
        try:
            page = await browser.new_page()
            await page.goto(base_url + "/", wait_until="networkidle", timeout=20000)
            # Let any initial SSE refresh settle so the board is stable
            await page.wait_for_timeout(2500)
            # Disable auto-refresh so board is not replaced during open/close cycles (avoids HTMX race)
            await page.evaluate("""() => {
              document.body.dataset.noAutoRefresh = '1';
              if (window.__refreshTimerId) clearTimeout(window.__refreshTimerId);
              window.__refreshTimerId = null;
            }""")

            cards = page.locator("[hx-get*='/api/ticket/']")
            await cards.first.wait_for(state="visible", timeout=10000)
            count = await cards.count()
            assert count >= 1, "Page must have at least one ticket card"

            for i in range(n):
                card = cards.nth(i % count)
                await card.scroll_into_view_if_needed()
                await card.click(force=True)
                try:
                    await page.wait_for_selector("#ticket-modal .modal-overlay", state="attached", timeout=10000)
                except Exception as e:
                    # Debug: save page state on failure
                    debug_path = _PROJECT_ROOT / "tests" / "e2e" / "failure_modal_open.html"
                    debug_path.write_text(await page.content(), encoding="utf-8")
                    await page.screenshot(path=str(_PROJECT_ROOT / "tests" / "e2e" / "failure_modal_open.png"))
                    raise AssertionError(
                        f"Modal did not open on iteration {i + 1}/{n}. Page saved to {debug_path}"
                    ) from e

                close_btn = page.get_by_role("button", name="Close")
                await close_btn.click()

                await page.wait_for_selector("#ticket-modal .modal-overlay", state="detached", timeout=5000)
        finally:
            await browser.close()
