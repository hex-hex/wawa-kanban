"""Pytest hooks and shared options for the test suite."""


def pytest_addoption(parser):
    parser.addoption(
        "--wawa-e2e-port",
        action="store",
        type=int,
        default=None,
        metavar="PORT",
        help=(
            "Port for browser e2e temporary uvicorn (tests/e2e/test_modal_open_close.py). "
            "Overrides WAWA_E2E_PORT; default when unset is 5022."
        ),
    )
