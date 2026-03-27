"""CLI behavior for ``wkanban`` (non-e2e)."""

import io
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from wawa_cli import project_commands


class _FakeTTYStdin(io.StringIO):
    """``StringIO`` that reports a TTY so interactive prompts run under pytest."""

    def isatty(self) -> bool:
        return True


def test_project_archive_stub_exit_code(capsys):
    from wawa_cli.main import main

    assert main(["project", "archive"]) == project_commands.STUB_EXIT_CODE
    err = capsys.readouterr().err
    assert "Not implemented yet" in err


def test_project_list_empty_workspace(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    (ws / "projects").mkdir(parents=True)
    assert main(["project", "list", "--workspace", str(ws)]) == 0
    assert capsys.readouterr().out.strip() == "No projects."


def test_project_list_sorted_names(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    (ws / "projects" / "wawa.proj.zed").mkdir(parents=True)
    (ws / "projects" / "wawa.proj.aaa").mkdir(parents=True)
    assert main(["project", "list", "--workspace", str(ws)]) == 0
    assert capsys.readouterr().out.strip().splitlines() == ["wawa.proj.aaa", "wawa.proj.zed"]


def test_project_list_skips_hidden_dirs(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    (ws / "projects" / "wawa.proj.visible").mkdir(parents=True)
    (ws / "projects" / ".hidden").mkdir(parents=True)
    assert main(["project", "list", "--workspace", str(ws)]) == 0
    assert capsys.readouterr().out.strip() == "wawa.proj.visible"


def test_project_list_workspace_missing(tmp_path, capsys, monkeypatch):
    from wawa_cli.main import main

    missing = tmp_path / "nope"
    monkeypatch.delenv("WAWA_WORKSPACE_PATH", raising=False)
    assert main(["project", "list", "--workspace", str(missing)]) == 1
    err = capsys.readouterr().err
    assert "Workspace not found" in err


def test_project_add_creates_layout(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()
    assert (
        main(["project", "add", "my-beta", "--workspace", str(ws), "--yes"]) == 0
    )
    out = capsys.readouterr().out
    proj = ws / "projects" / "wawa.proj.my-beta"
    assert proj.is_dir()
    assert (proj / "project.md").is_file()
    assert (proj / ".project.location").is_file()
    for sub in ("todos", "waiting_for_verification", "finished"):
        assert (proj / sub).is_dir()
    assert str(proj) in out


def test_project_add_accepts_full_id(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()
    assert (
        main(
            [
                "project",
                "add",
                "wawa.proj.custom-id",
                "--workspace",
                str(ws),
                "-y",
            ]
        )
        == 0
    )
    assert (ws / "projects" / "wawa.proj.custom-id" / "todos").is_dir()


def test_project_add_duplicate_rejects_second_call(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()
    argv = ["project", "add", "dup", "--workspace", str(ws), "-y"]
    assert main(argv) == 0
    assert main(argv) == 1
    err = capsys.readouterr().err
    assert "duplicate" in err.lower() or "Refusing" in err


def test_project_add_decline_prompt(tmp_path, capsys, monkeypatch):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin("n\n"))
    assert main(["project", "add", "nope", "--workspace", str(ws)]) == 1
    assert "Aborted." in capsys.readouterr().err
    assert not (ws / "projects").exists()


def test_project_add_confirm_prompt_default_y(tmp_path, capsys, monkeypatch):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin("\n"))
    assert main(["project", "add", "yes-proj", "--workspace", str(ws)]) == 0
    assert (ws / "projects" / "wawa.proj.yes-proj").is_dir()


def test_project_list_uses_fixtures_workspace(monkeypatch, capsys):
    """When WAWA_WORKSPACE_PATH points at fixtures/workspace, list matches project dirs."""
    from wawa_cli.main import main

    root = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"
    monkeypatch.setenv("WAWA_WORKSPACE_PATH", str(root))
    assert main(["project", "list"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert set(lines) == {"wawa.proj.another", "wawa.proj.default"}


def test_todo_lists_md_tickets_with_created_time_and_location(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    p1 = ws / "projects" / "wawa.proj.alpha"
    p2 = ws / "projects" / "wawa.proj.beta"
    (p1 / "todos").mkdir(parents=True)
    (p2 / "todos").mkdir(parents=True)

    (p1 / ".project.location").write_text("/repo/alpha\n", encoding="utf-8")
    # beta has empty .project.location (or missing) -> no third column.
    (p2 / ".project.location").write_text("\n", encoding="utf-8")

    (p1 / "todos" / "wawa.proj.alpha.implementation.first-task.md").write_text("a", encoding="utf-8")
    (p1 / "todos" / "wawa.proj.alpha.design.locked.md.lock").write_text("x", encoding="utf-8")
    (p2 / "todos" / "wawa.proj.beta.websearch.research-topic.md").write_text("b", encoding="utf-8")

    rc = main(["todo", "--workspace", str(ws)])
    assert rc == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert any(line.startswith("alpha.first-task\t") and line.endswith("\t/repo/alpha") for line in lines)
    assert any(line.startswith("beta.research-topic\t") and line.count("\t") == 1 for line in lines)


def test_ticket_locate_ok_for_implementation_git_repo(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    project = ws / "projects" / "wawa.proj.demo"
    todos = project / "todos"
    todos.mkdir(parents=True)

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (project / ".project.location").write_text(str(repo), encoding="utf-8")

    ticket = todos / "wawa.proj.demo.implementation.sample-task.md"
    ticket.write_text("x", encoding="utf-8")

    rc = main(["ticket", "locate", "demo.sample-task", "--workspace", str(ws), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["status"] == "ok"
    assert data["mode"] == "implementation"
    assert data["project_id"] == "wawa.proj.demo"
    assert data["slug"] == "sample-task"
    assert data["ticket_path"].endswith(ticket.name)
    assert data["repo_path"] == str(repo.resolve())
    assert data["target_worktree"].endswith("/.wawa/worktrees/sample-task")
    assert data["target_branch"] == "worktree-sample-task"


def test_ticket_locate_warning_for_non_implementation(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    project = ws / "projects" / "wawa.proj.demo"
    todos = project / "todos"
    todos.mkdir(parents=True)
    (project / ".project.location").write_text(str(tmp_path / "repo"), encoding="utf-8")
    (todos / "wawa.proj.demo.design.sample-task.md").write_text("x", encoding="utf-8")

    rc = main(["ticket", "locate", "demo.sample-task", "--workspace", str(ws), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["status"] == "warning"
    assert "not implementation" in data["message"]


def test_ticket_locate_warning_for_missing_or_non_git_repo(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    project = ws / "projects" / "wawa.proj.demo"
    todos = project / "todos"
    todos.mkdir(parents=True)
    (todos / "wawa.proj.demo.implementation.sample-task.md").write_text("x", encoding="utf-8")

    # Missing repo path
    missing = tmp_path / "missing-repo"
    (project / ".project.location").write_text(str(missing), encoding="utf-8")
    rc = main(["ticket", "locate", "demo.sample-task", "--workspace", str(ws), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["status"] == "warning"
    assert "does not exist" in data["message"]

    # Existing but not git
    repo = tmp_path / "plain-dir"
    repo.mkdir()
    (project / ".project.location").write_text(str(repo), encoding="utf-8")
    rc = main(["ticket", "locate", "demo.sample-task", "--workspace", str(ws), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["status"] == "warning"
    assert "not a git repository" in data["message"]


def test_ticket_locate_errors_on_duplicate_slug(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    project = ws / "projects" / "wawa.proj.demo"
    todos = project / "todos"
    waiting = project / "waiting_for_verification"
    todos.mkdir(parents=True)
    waiting.mkdir(parents=True)
    (project / ".project.location").write_text(str(tmp_path / "repo"), encoding="utf-8")

    (todos / "wawa.proj.demo.implementation.same-slug.md").write_text("a", encoding="utf-8")
    (waiting / "wawa.proj.demo.implementation.same-slug.md").write_text("b", encoding="utf-8")

    rc = main(["ticket", "locate", "demo.same-slug", "--workspace", str(ws), "--format", "json"])
    assert rc == 1
    assert "multiple tickets" in capsys.readouterr().err


def test_project_procress_default_is_dry_run_and_prints_plan(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    proj = ws / "projects" / "wawa.proj.demo"
    todos = proj / "todos"
    waiting = proj / "waiting_for_verification"
    finished = proj / "finished"
    for d in (todos, waiting, finished):
        d.mkdir(parents=True, exist_ok=True)

    # Agent slots: one busy developer + two free developers.
    dev_busy = ws / "agents" / "developers" / "busy"
    dev_default = ws / "agents" / "developers" / "default"
    dev_free2 = ws / "agents" / "developers" / "free2"
    des_default = ws / "agents" / "designers" / "default"
    ver_code_default = ws / "agents" / "code-verifiers" / "default"
    for d in (dev_busy, dev_default, dev_free2, des_default, ver_code_default):
        d.mkdir(parents=True, exist_ok=True)

    (dev_busy / "wawa.proj.other.implementation.existing.md").write_text("x", encoding="utf-8")

    t_old = todos / "wawa.proj.demo.implementation.oldest.md"
    t_old.write_text("old", encoding="utf-8")
    time.sleep(0.02)  # Ensure ctime order is deterministic.
    t_new = todos / "wawa.proj.demo.implementation.newer.md"
    t_new.write_text("new", encoding="utf-8")
    (todos / "wawa.proj.demo.design.ui.md").write_text("design", encoding="utf-8")
    (todos / "wawa.proj.demo.websearch.skip-lock.md.lock").write_text("lock", encoding="utf-8")
    (waiting / "wawa.proj.demo.implementation.verify.md").write_text("verify", encoding="utf-8")

    rc = main(["project", "procress", "demo", "--workspace", str(ws)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry_run=yes" in out
    assert "planned=4" in out
    assert "moved=0" in out
    assert "PLAN:" in out

    # Dry-run should not move files.
    assert t_old.is_file()
    assert t_new.is_file()
    assert (todos / "wawa.proj.demo.design.ui.md").is_file()
    assert (waiting / "wawa.proj.demo.implementation.verify.md").is_file()
    assert not (dev_default / t_old.name).exists()
    assert not (dev_free2 / t_new.name).exists()
    assert not (des_default / "wawa.proj.demo.design.ui.md").exists()
    assert not (ver_code_default / "wawa.proj.demo.implementation.verify.md").exists()
    # Lock ticket is ignored and remains in source dir.
    assert (todos / "wawa.proj.demo.websearch.skip-lock.md.lock").is_file()


def test_project_procress_exec_moves_pending_tickets_by_mode_and_ctime(tmp_path, capsys):
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    proj = ws / "projects" / "wawa.proj.demo"
    todos = proj / "todos"
    waiting = proj / "waiting_for_verification"
    finished = proj / "finished"
    for d in (todos, waiting, finished):
        d.mkdir(parents=True, exist_ok=True)

    dev_busy = ws / "agents" / "developers" / "busy"
    dev_default = ws / "agents" / "developers" / "default"
    dev_free2 = ws / "agents" / "developers" / "free2"
    des_default = ws / "agents" / "designers" / "default"
    ver_code_default = ws / "agents" / "code-verifiers" / "default"
    for d in (dev_busy, dev_default, dev_free2, des_default, ver_code_default):
        d.mkdir(parents=True, exist_ok=True)
    (dev_busy / "wawa.proj.other.implementation.existing.md").write_text("x", encoding="utf-8")

    t_old = todos / "wawa.proj.demo.implementation.oldest.md"
    t_old.write_text("old", encoding="utf-8")
    time.sleep(0.02)
    t_new = todos / "wawa.proj.demo.implementation.newer.md"
    t_new.write_text("new", encoding="utf-8")
    (todos / "wawa.proj.demo.design.ui.md").write_text("design", encoding="utf-8")
    (waiting / "wawa.proj.demo.implementation.verify.md").write_text("verify", encoding="utf-8")

    rc = main(["project", "procress", "demo", "--workspace", str(ws), "--exec"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry_run=no" in out
    assert "planned=4" in out
    assert "moved=4" in out

    assert (dev_default / t_old.name).is_file()
    assert (dev_free2 / t_new.name).is_file()
    assert (des_default / "wawa.proj.demo.design.ui.md").is_file()
    assert (ver_code_default / "wawa.proj.demo.implementation.verify.md").is_file()


def _write_openclaw_config(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_agent_list_sorted_ids(tmp_path, monkeypatch, capsys):
    from wawa_cli.main import main

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_config(
        cfg,
        {
            "agents": {
                "list": [
                    {"id": "zebra", "name": "Z"},
                    {"id": "alpha", "name": "A"},
                ]
            }
        },
    )
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(cfg))
    assert main(["agent", "list"]) == 0
    assert capsys.readouterr().out.strip().splitlines() == ["alpha", "zebra"]


def test_agent_list_empty(monkeypatch, capsys, tmp_path):
    from wawa_cli.main import main

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_config(cfg, {"agents": {"list": []}})
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(cfg))
    assert main(["agent", "list"]) == 0
    assert capsys.readouterr().out.strip() == "No agents."


def test_agent_list_long_format(tmp_path, monkeypatch, capsys):
    from wawa_cli.main import main

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_config(
        cfg,
        {
            "agents": {
                "list": [
                    {"id": "b", "name": "Bee"},
                    {"id": "a", "name": ""},
                ]
            }
        },
    )
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(cfg))
    assert main(["agent", "list", "--long"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == ["a\t", "b\tBee"]


def test_agent_add_default_creates_slot_dirs(tmp_path, monkeypatch, capsys):
    from wawa_cli import agent_commands
    from wawa_cli.main import main

    ws = tmp_path / "ws"
    ws.mkdir()

    def fake_init(**_kwargs):
        return 0

    monkeypatch.setattr(agent_commands, "run_init_agents", fake_init)
    assert main(["agent", "add-default", "--workspace", str(ws)]) == 0
    assert (ws / "agents" / "designers" / "default").is_dir()
    assert (ws / "agents" / "developers" / "default").is_dir()
    assert (ws / "agents" / "info-officers" / "default").is_dir()
    assert (ws / "agents" / "code-verifiers" / "default").is_dir()
    assert (ws / "agents" / "general-verifiers" / "default").is_dir()


def test_agent_add_default_workspace_missing(tmp_path, capsys):
    from wawa_cli.main import main

    missing = tmp_path / "nope"
    assert main(["agent", "add-default", "--workspace", str(missing)]) == 1
    assert "Workspace not found" in capsys.readouterr().err


def test_agent_sync_dispatches_to_openclaw_sync(tmp_path, monkeypatch):
    from wawa_cli import agent_commands
    from wawa_cli.main import main

    called = {}

    def fake_sync(*, config=None, state_dir=None, repo=None):
        called["config"] = config
        called["state_dir"] = state_dir
        called["repo"] = repo
        return 0

    monkeypatch.setattr(agent_commands, "run_sync_agents", fake_sync)

    cfg = tmp_path / "cfg.json"
    st = tmp_path / "state"
    rp = tmp_path / "repo"
    assert main(["agent", "sync", "--config", str(cfg), "--state-dir", str(st), "--repo", str(rp)]) == 0
    assert called["config"] == cfg
    assert called["state_dir"] == st
    assert called["repo"] == rp


def test_agent_subparser_requires_known_subcommand():
    from wawa_cli.main import main

    with pytest.raises(SystemExit):
        main(["agent", "unknown-subcommand"])


def test_agent_list_wawa_only_filters(tmp_path, monkeypatch, capsys):
    from wawa_cli.main import main

    wawa_root = tmp_path / "wawa_ws"
    inside = wawa_root / "nested"
    inside.mkdir(parents=True)
    outside = tmp_path / "outside_openclaw"
    outside.mkdir()

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_config(
        cfg,
        {
            "agents": {
                "list": [
                    {
                        "id": "wawa-inside",
                        "name": "In",
                        "workspace": str(inside.resolve()),
                    },
                    {
                        "id": "wawa-outside",
                        "name": "Out",
                        "workspace": str(outside.resolve()),
                    },
                    {"id": "plain-other", "name": "O", "workspace": str(inside.resolve())},
                ]
            }
        },
    )
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(cfg))
    assert main(
        ["agent", "list", "--wawa-only", "--wawa-workspace", str(wawa_root.resolve())]
    ) == 0
    assert capsys.readouterr().out.strip().splitlines() == ["wawa-inside"]
