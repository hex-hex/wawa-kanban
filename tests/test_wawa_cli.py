"""CLI behavior for ``wkanban`` (non-e2e)."""

import pytest

from wawa_cli import project_commands


@pytest.mark.parametrize(
    "argv",
    [
        ["project", "add"],
        ["project", "archive"],
        ["project", "list"],
    ],
)
def test_project_subcommands_stub_exit_code(argv, capsys):
    from wawa_cli.main import main

    assert main(argv) == project_commands.STUB_EXIT_CODE
    err = capsys.readouterr().err
    assert "Not implemented yet" in err
