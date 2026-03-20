from __future__ import annotations

from pathlib import Path

import pytest

from wawa_openclaw.agents_ops import (
    materialize_agent,
    merge_agent_into_config,
    plan_add_agent,
    remove_agent_from_config,
)
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config


def test_plan_add_materialize_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    role_dir = repo / "agents" / "designer"
    role_dir.mkdir(parents=True)
    (role_dir / "AGENTS.md").write_text("hello", encoding="utf-8")

    state = tmp_path / "openclaw"
    entry, workspace, agent_dir, role_src = plan_add_agent(
        name="My Agent", role="designer", root=repo, state=state
    )
    assert entry["id"] == "my-agent"
    assert "workspace-wawa-my-agent" in entry["workspace"]

    cfg: dict = {}
    ensure_agents_tree(cfg)
    merge_agent_into_config(cfg, entry)
    assert len(cfg["agents"]["list"]) == 1

    materialize_agent(workspace=workspace, agent_dir=agent_dir, role_src=role_src)
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "hello"
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


def test_plan_rejects_unknown_role(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown role"):
        plan_add_agent(name="a", role="not-a-role", root=tmp_path, state=tmp_path)
