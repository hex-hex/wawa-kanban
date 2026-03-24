"""Task modes (websearch / codesearch) and agent-folder mode filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.models.kanban import TaskMode, TicketStatus


def test_parse_filename_websearch_and_codesearch() -> None:
    from src.services.tickets import _parse_filename

    p, m, slug = _parse_filename("wawa.proj.default.websearch.payment-flow.md")
    assert p == "wawa.proj.default"
    assert m == TaskMode.WEBSEARCH
    assert slug == "payment-flow"

    p2, m2, slug2 = _parse_filename("wawa.proj.default.codesearch.api-integration.md")
    assert p2 == "wawa.proj.default"
    assert m2 == TaskMode.CODESEARCH
    assert slug2 == "api-integration"


def test_fixture_workspace_has_expected_verifying_websearch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """General-verifier folder tickets with websearch mode appear under Verifying."""
    from src.services import tickets as tickets_mod

    root = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"
    monkeypatch.setattr(tickets_mod, "WORKSPACE_PATH", root / "projects")
    monkeypatch.setattr(tickets_mod, "AGENTS_WORKSPACE_PATH", root / "agents")

    from src.services.tickets import _load_project

    project = _load_project(root / "projects" / "wawa.proj.default")
    assert project is not None
    ids_modes = {(t["id"], t["mode"], t["status"]) for t in project["tickets"]}
    assert ("TICKET-009", TaskMode.WEBSEARCH, TicketStatus.VERIFYING) in ids_modes
    assert ("TICKET-LONG-FIXTURE", TaskMode.WEBSEARCH, TicketStatus.VERIFYING) in ids_modes


def test_fixture_workspace_has_info_officer_queue_websearch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Info-officer folder tickets with websearch mode appear under In Progress."""
    from src.services import tickets as tickets_mod

    root = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"
    monkeypatch.setattr(tickets_mod, "WORKSPACE_PATH", root / "projects")
    monkeypatch.setattr(tickets_mod, "AGENTS_WORKSPACE_PATH", root / "agents")

    from src.services.tickets import _load_project

    project = _load_project(root / "projects" / "wawa.proj.default")
    assert project is not None
    ids_modes = {(t["id"], t["mode"], t["status"]) for t in project["tickets"]}
    assert ("TICKET-INFO-FIXTURE", TaskMode.WEBSEARCH, TicketStatus.IN_PROGRESS) in ids_modes


def test_fixture_workspace_has_code_verifier_queue_implementation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Code-verifier folder tickets with implementation mode appear under Verifying."""
    from src.services import tickets as tickets_mod

    root = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"
    monkeypatch.setattr(tickets_mod, "WORKSPACE_PATH", root / "projects")
    monkeypatch.setattr(tickets_mod, "AGENTS_WORKSPACE_PATH", root / "agents")

    from src.services.tickets import _load_project

    project = _load_project(root / "projects" / "wawa.proj.default")
    assert project is not None
    ids_modes = {(t["id"], t["mode"], t["status"]) for t in project["tickets"]}
    assert ("TICKET-CODE-VERIFY-FIXTURE", TaskMode.IMPLEMENTATION, TicketStatus.VERIFYING) in ids_modes


def test_wrong_mode_not_merged_from_agent_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tickets in an agent folder are omitted when filename mode does not match that slot."""
    from src.services import tickets as tickets_mod

    root = tmp_path / "ws"
    (root / "projects" / "wawa.proj.x" / "todos").mkdir(parents=True)
    (root / "agents" / "developers" / "default").mkdir(parents=True)
    (root / "agents" / "info-officers" / "default").mkdir(parents=True)
    (root / "agents" / "code-verifiers" / "default").mkdir(parents=True)
    (root / "agents" / "general-verifiers" / "default").mkdir(parents=True)

    (root / "agents" / "developers" / "default" / "wawa.proj.x.websearch.wrong-slot.md").write_text(
        "---\nid: BAD-DEV-WEB\n---\n\nbody\n",
        encoding="utf-8",
    )
    (root / "agents" / "info-officers" / "default" / "wawa.proj.x.websearch.right-slot.md").write_text(
        "---\nid: GOOD-INFO\n---\n\nbody\n",
        encoding="utf-8",
    )
    (root / "agents" / "code-verifiers" / "default" / "wawa.proj.x.websearch.wrong-verifier.md").write_text(
        "---\nid: BAD-CV-WEB\n---\n\nbody\n",
        encoding="utf-8",
    )
    (root / "agents" / "general-verifiers" / "default" / "wawa.proj.x.websearch.right-verifier.md").write_text(
        "---\nid: GOOD-GV-WEB\n---\n\nbody\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(tickets_mod, "WORKSPACE_PATH", root / "projects")
    monkeypatch.setattr(tickets_mod, "AGENTS_WORKSPACE_PATH", root / "agents")

    from src.services.tickets import _load_project

    project = _load_project(root / "projects" / "wawa.proj.x")
    assert project is not None
    ids = {t["id"] for t in project["tickets"]}
    assert "GOOD-INFO" in ids
    assert "GOOD-GV-WEB" in ids
    assert "BAD-DEV-WEB" not in ids
    assert "BAD-CV-WEB" not in ids
