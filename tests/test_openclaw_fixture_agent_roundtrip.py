"""Add/remove agent roundtrip against fixtures/openclaw layout and config parity."""

from __future__ import annotations

import json
import shutil
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest

from wawa_openclaw.agents_ops import remove_agent_from_config
from wawa_openclaw.cli import run_add, run_remove
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_OPENCLAW_JSON = REPO_ROOT / "fixtures" / "openclaw" / "openclaw.json"


def _assert_new_agent_workspace_matches_role_template(
    workspace: Path, *, role: str, repo: Path = REPO_ROOT
) -> None:
    """After ``materialize_agent``, workspace must mirror ``agents/<role>/`` (files + nested dirs, skip dotfiles)."""
    role_src = repo / "agents" / role
    assert role_src.is_dir(), f"Missing role template: {role_src}"
    assert workspace.is_dir(), f"Workspace is not a directory: {workspace}"

    for src in sorted(role_src.rglob("*")):
        if src.name.startswith("."):
            continue
        rel = src.relative_to(role_src)
        dest = workspace / rel
        if src.is_dir():
            assert dest.is_dir(), f"Expected directory {rel} under workspace"
        else:
            assert dest.is_file(), f"Expected file {rel} under workspace"
            assert dest.read_bytes() == src.read_bytes(), f"Content mismatch for {rel}"


def _canonical_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Stable deep structure for equality after JSON5 save/load."""
    return json.loads(json.dumps(d, sort_keys=True))


def test_remove_strips_bindings_and_telegram_account_from_binding_match() -> None:
    cfg = {
        "agents": {
            "defaults": {},
            "list": [
                {"id": "wawa-test", "name": "wawa-test", "workspace": "/x/ws", "agentDir": "/x/a"},
            ],
        },
        "bindings": [
            {"agentId": "wawa-test", "match": {"channel": "telegram", "accountId": "wawa-test"}},
        ],
        "channels": {
            "telegram": {
                "accounts": {
                    "wawa-test": {"botToken": "yyyy", "dmPolicy": "pairing"},
                    "keep-me": {},
                }
            }
        },
    }
    ensure_agents_tree(cfg)
    remove_agent_from_config(cfg, "wawa-test")
    assert cfg["agents"]["list"] == []
    assert cfg["bindings"] == []
    assert "wawa-test" not in cfg["channels"]["telegram"]["accounts"]
    assert "keep-me" in cfg["channels"]["telegram"]["accounts"]


def test_remove_strips_agent_nested_heartbeat_and_sandbox_with_list_entry() -> None:
    """Per-agent channel / heartbeat / sandbox live on the agent object; removing the agent drops them."""
    cfg = {
        "agents": {
            "defaults": {},
            "list": [
                {
                    "id": "wawa-rich",
                    "name": "Rich",
                    "workspace": "/tmp/ws",
                    "agentDir": "/tmp/ad",
                    "heartbeat": {"intervalSeconds": 30},
                    "sandbox": {"mode": "off"},
                },
            ],
        },
        "bindings": [],
    }
    ensure_agents_tree(cfg)
    remove_agent_from_config(cfg, "wawa-rich")
    assert cfg["agents"]["list"] == []


def test_add_remove_roundtrip_matches_fixture_openclaw_snapshot(tmp_path: Path) -> None:
    if not FIXTURE_OPENCLAW_JSON.is_file():
        pytest.skip("fixtures/openclaw/openclaw.json missing")

    config_path = tmp_path / "openclaw.json"
    state_dir = tmp_path / "openclaw_state"
    shutil.copyfile(FIXTURE_OPENCLAW_JSON, config_path)

    initial = load_config(config_path)
    snapshot = _canonical_dict(initial)

    add_args = Namespace(
        name="FixtureRoundtrip",
        role="designer",
        config=config_path,
        state_dir=state_dir,
        repo=REPO_ROOT,
    )
    assert run_add(add_args) == 0

    after_add = load_config(config_path)
    ids = [a.get("id") for a in after_add["agents"]["list"] if isinstance(a, dict)]
    assert "wawa-fixtureroundtrip" in ids

    entry = next(
        a for a in after_add["agents"]["list"] if isinstance(a, dict) and a.get("id") == "wawa-fixtureroundtrip"
    )
    assert entry.get("name") == "wawa-FixtureRoundtrip"
    assert "workspace" in entry and "agentDir" in entry

    ws = state_dir / "workspace-wawa-wawa-fixtureroundtrip"
    ad = state_dir / "agents" / "wawa-fixtureroundtrip" / "agent"
    assert ws.is_dir()
    assert (ws / "AGENTS.md").is_file()
    assert ad.is_dir()
    _assert_new_agent_workspace_matches_role_template(ws, role="designer", repo=REPO_ROOT)
    # Config paths must point at this workspace and agentDir on disk
    assert Path(entry["workspace"]).expanduser().resolve() == ws.resolve()
    assert Path(entry["agentDir"]).expanduser().resolve() == ad.resolve()

    remove_args = Namespace(
        name="FixtureRoundtrip",
        purge=True,
        yes=True,
        config=config_path,
        state_dir=state_dir,
    )
    assert run_remove(remove_args) == 0

    assert not ws.exists()
    assert not (state_dir / "agents" / "wawa-fixtureroundtrip").exists()

    final = load_config(config_path)
    assert _canonical_dict(final) == snapshot


def test_synthetic_agent_with_binding_channel_heartbeat_roundtrip_to_initial_file(tmp_path: Path) -> None:
    """Start from a minimal file mirroring fixture sections; after add+manual extras+remove, file matches initial."""
    initial_path = tmp_path / "openclaw.json"
    initial_path.write_text(
        json.dumps(
            {
                "agents": {"defaults": {}, "list": [{"id": "main", "default": True}]},
                "bindings": [],
                "channels": {
                    "telegram": {
                        "enabled": True,
                        "accounts": {"main": {"botToken": "x"}},
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    snapshot = _canonical_dict(load_config(initial_path))

    state_dir = tmp_path / "state"
    add_args = Namespace(
        name="ChanTest",
        role="designer",
        config=initial_path,
        state_dir=state_dir,
        repo=REPO_ROOT,
    )
    assert run_add(add_args) == 0

    ws_ch = state_dir / "workspace-wawa-wawa-chantest"
    _assert_new_agent_workspace_matches_role_template(ws_ch, role="designer", repo=REPO_ROOT)

    cfg = load_config(initial_path)
    agent_id = "wawa-chantest"
    cfg.setdefault("bindings", []).append(
        {
            "agentId": agent_id,
            "match": {"channel": "telegram", "accountId": agent_id},
        }
    )
    ch = cfg["channels"]["telegram"].setdefault("accounts", {})
    ch[agent_id] = {"botToken": "zzzz", "dmPolicy": "pairing"}
    for a in cfg["agents"]["list"]:
        if isinstance(a, dict) and a.get("id") == agent_id:
            a["heartbeat"] = {"intervalSeconds": 120}
            a["sandbox"] = {"mode": "off"}
            break
    save_config(initial_path, cfg)

    remove_args = Namespace(
        name="ChanTest",
        purge=True,
        yes=True,
        config=initial_path,
        state_dir=state_dir,
    )
    assert run_remove(remove_args) == 0

    final = load_config(initial_path)
    assert _canonical_dict(final) == snapshot
