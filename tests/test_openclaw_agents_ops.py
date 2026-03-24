from __future__ import annotations

import shutil
from argparse import Namespace
from pathlib import Path

import pytest

from wawa_openclaw.agents_ops import (
    ROLES_DISALLOWED_FOR_MANUAL_ADD,
    build_agent_template_context,
    identity_display_name_from,
    kanban_slot_from_agent_id,
    materialize_agent,
    merge_agent_into_config,
    plan_add_agent,
    remove_agent_from_config,
    render_agent_list_entry,
    slugify_agent_id,
)
from wawa_openclaw.cli import run_add
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config
from wawa_openclaw.paths import to_config_path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Minimal agent.json.j2 (same shape as production). Expected merged entry is asserted explicitly.
_MINIMAL_AGENT_JSON_J2 = """{
  "id": {{ agent_id | tojson }},
  "name": {{ agent_display_name | tojson }},
  "workspace": {{ workspace_path | tojson }},
  "agentDir": {{ agent_dir_path | tojson }}
}
"""


def test_plan_add_materialize_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    role_dir = repo / "agents" / "designer"
    role_dir.mkdir(parents=True)
    (role_dir / "AGENTS.md.j2").write_text("slot={{ kanban_slot }}", encoding="utf-8")
    (role_dir / "agent.json.j2").write_text(_MINIMAL_AGENT_JSON_J2, encoding="utf-8")

    state = tmp_path / "openclaw"
    entry, workspace, agent_dir, role_src = plan_add_agent(
        name="wawa-my-agent", role="designer", root=repo, state=state
    )
    expected_entry = {
        "id": "wawa-my-agent",
        "name": "wawa-my-agent",
        "workspace": to_config_path(workspace),
        "agentDir": to_config_path(agent_dir),
    }
    assert entry == expected_entry

    cfg: dict = {}
    ensure_agents_tree(cfg)
    merge_agent_into_config(cfg, entry)
    assert len(cfg["agents"]["list"]) == 1

    materialize_agent(
        workspace=workspace,
        agent_dir=agent_dir,
        role_src=role_src,
        agent_id=entry["id"],
        agent_display_name=entry["name"],
        role="designer",
    )
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "slot=my-agent"
    assert agent_dir.is_dir()


def test_remove_strips_bindings(tmp_path: Path) -> None:
    cfg = {
        "agents": {
            "list": [{"id": "x", "name": "X"}],
        },
        "bindings": [{"agentId": "x", "match": {}}],
    }
    ensure_agents_tree(cfg)
    remove_agent_from_config(cfg, "x")
    assert cfg["agents"]["list"] == []
    assert cfg["bindings"] == []


def test_save_load_json5_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "openclaw.json"
    data = {"agents": {"defaults": {}, "list": [{"id": "main"}]}}
    save_config(p, data)
    loaded = load_config(p)
    assert loaded["agents"]["list"][0]["id"] == "main"
    text = p.read_text(encoding="utf-8")
    assert '"id"' in text


_AGENT_JSON_J2_WITH_HEARTBEAT = """{
  "id": {{ agent_id | tojson }},
  "name": {{ agent_display_name | tojson }},
  "workspace": {{ workspace_path | tojson }},
  "agentDir": {{ agent_dir_path | tojson }},
  "heartbeat": {"every": "42s", "target": "none"},
  "tag": {{ kanban_slot | tojson }}
}
"""


def test_render_agent_list_entry_from_agent_json_j2(tmp_path: Path) -> None:
    role_dir = tmp_path / "role"
    role_dir.mkdir()
    (role_dir / "agent.json.j2").write_text(_AGENT_JSON_J2_WITH_HEARTBEAT, encoding="utf-8")
    ws = tmp_path / "workspace-wawa-x"
    ad = tmp_path / "agents" / "wawa-x" / "agent"
    entry = render_agent_list_entry(
        role_dir,
        agent_id="wawa-x",
        agent_display_name="wawa-X",
        role="developer",
        workspace=ws,
        agent_dir=ad,
    )
    expected = {
        "id": "wawa-x",
        "name": "wawa-X",
        "workspace": to_config_path(ws),
        "agentDir": to_config_path(ad),
        "heartbeat": {"every": "42s", "target": "none"},
        "tag": "x",
    }
    assert entry == expected


def test_render_agent_list_entry_invalid_json_raises(tmp_path: Path) -> None:
    role_dir = tmp_path / "role"
    role_dir.mkdir()
    (role_dir / "agent.json.j2").write_text("{not json", encoding="utf-8")
    ws = tmp_path / "w"
    ad = tmp_path / "a"
    with pytest.raises(ValueError, match="Invalid JSON"):
        render_agent_list_entry(
            role_dir,
            agent_id="wawa-x",
            agent_display_name="wawa-X",
            role="developer",
            workspace=ws,
            agent_dir=ad,
        )


def test_save_config_backs_up_before_overwrite(tmp_path: Path) -> None:
    p = tmp_path / "openclaw.json"
    backup = tmp_path / "openclaw.json.bak.wawa"
    p.write_text('{"before": true}', encoding="utf-8")
    save_config(p, {"agents": {"defaults": {}, "list": []}})
    assert backup.is_file()
    assert backup.read_text(encoding="utf-8") == '{"before": true}'
    assert '"before"' not in p.read_text(encoding="utf-8")
    save_config(p, {"agents": {"defaults": {}, "list": [{"id": "x"}]}})
    assert backup.read_text(encoding="utf-8").strip().startswith("{")
    loaded = load_config(backup)
    assert loaded.get("agents", {}).get("list") == []


def test_plan_rejects_unknown_role(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown role"):
        plan_add_agent(name="a", role="not-a-role", root=tmp_path, state=tmp_path)


@pytest.mark.parametrize("role", sorted(ROLES_DISALLOWED_FOR_MANUAL_ADD))
def test_run_add_rejects_single_instance_roles(tmp_path: Path, role: str) -> None:
    args = Namespace(
        name="extra",
        role=role,
        config=tmp_path / "missing.json",
        state_dir=tmp_path,
        repo=tmp_path,
        yes=True,
        wawa_workspace=None,
    )
    assert run_add(args) == 1


def test_kanban_slot_and_identity_display_name() -> None:
    assert kanban_slot_from_agent_id("wawa-alice") == "alice"
    assert kanban_slot_from_agent_id("naked-id") == "naked-id"
    assert identity_display_name_from("wawa-Alice") == "Alice"
    assert identity_display_name_from("plain") == "plain"


def test_build_agent_template_context_has_ticket_folder_for_developer() -> None:
    ctx = build_agent_template_context(
        agent_id="wawa-dev1",
        agent_display_name="wawa-dev1",
        role="developer",
    )
    assert ctx["kanban_slot"] == "dev1"
    assert ctx["kanban_ticket_folder"] == "workspace/agents/developers/dev1/"
    assert ctx["kanban_type_folder"] == "developers"


def test_identity_agent_call_name_default_slot_vs_custom() -> None:
    ctx_default = build_agent_template_context(
        agent_id=slugify_agent_id("wawa-designer"),
        agent_display_name="wawa-designer",
        role="designer",
    )
    assert ctx_default["identity_agent_call_name"] == "Default Designer"

    ctx_pm = build_agent_template_context(
        agent_id=slugify_agent_id("wawa-project-manager"),
        agent_display_name="wawa-project-manager",
        role="project-manager",
    )
    assert ctx_pm["identity_agent_call_name"] == "Default Project Manager"

    ctx_custom = build_agent_template_context(
        agent_id="wawa-alice",
        agent_display_name="wawa-Alice",
        role="designer",
    )
    assert ctx_custom["identity_agent_call_name"] == "Alice"


def test_run_add_rejects_duplicate_agent_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(REPO_ROOT / "agents" / "designer", repo / "agents" / "designer")
    cfg_path = tmp_path / "openclaw.json"
    cfg: dict = {
        "agents": {
            "defaults": {},
            "list": [
                {
                    "id": "wawa-dup",
                    "name": "wawa-dup",
                    "workspace": "/x/ws",
                    "agentDir": "/x/ad",
                },
            ],
        },
    }
    ensure_agents_tree(cfg)
    save_config(cfg_path, cfg)

    args = Namespace(
        name="dup",
        role="designer",
        config=cfg_path,
        state_dir=tmp_path / "st",
        repo=repo,
        yes=True,
        wawa_workspace=None,
    )
    assert run_add(args) == 1


def test_run_add_requires_tty_or_yes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(REPO_ROOT / "agents" / "designer", repo / "agents" / "designer")
    cfg_path = tmp_path / "openclaw.json"
    save_config(cfg_path, {"agents": {"defaults": {}, "list": []}})
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    args = Namespace(
        name="newone",
        role="designer",
        config=cfg_path,
        state_dir=tmp_path / "st",
        repo=repo,
        yes=False,
        wawa_workspace=None,
    )
    assert run_add(args) == 1
