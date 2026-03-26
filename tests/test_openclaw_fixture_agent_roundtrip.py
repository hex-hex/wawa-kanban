"""Add/remove agent roundtrip against fixtures/openclaw layout and config parity."""

from __future__ import annotations

import json
import shutil
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment

from wawa_openclaw.agents_ops import (
    AGENT_JSON_J2,
    ROLES_ALLOWED_FOR_MANUAL_ADD,
    build_agent_template_context,
    remove_agent_from_config,
    slugify_agent_id,
)
from wawa_openclaw.cli import run_add, run_remove
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_OPENCLAW_JSON = REPO_ROOT / "fixtures" / "openclaw" / "openclaw.json"


def _assert_workspace_matches_rendered_j2(
    workspace: Path,
    *,
    role: str,
    repo: Path,
    agent_id: str,
    agent_display_name: str,
) -> None:
    """Workspace ``*.md`` must equal rendering each ``*.md.j2`` under ``agents/<role>/`` with the same context."""
    role_src = repo / "agents" / role
    assert role_src.is_dir(), f"Missing role template: {role_src}"
    assert workspace.is_dir(), f"Workspace is not a directory: {workspace}"

    ctx = build_agent_template_context(
        agent_id=agent_id,
        agent_display_name=agent_display_name,
        role=role,
    )
    env = Environment(autoescape=False)

    for src in sorted(role_src.rglob("*")):
        if src.name.startswith("."):
            continue
        rel = src.relative_to(role_src)
        if src.is_dir():
            assert (workspace / rel).is_dir(), f"Expected directory {rel}"
            continue
        if src.name == AGENT_JSON_J2:
            continue
        if src.name.endswith(".md.j2"):
            out_name = src.name[:-3]
            parent = workspace / rel.parent
            dest = parent / out_name
            rendered = env.from_string(src.read_text(encoding="utf-8")).render(**ctx)
            assert dest.is_file(), f"Expected rendered file {dest}"
            assert dest.read_text(encoding="utf-8") == rendered, f"Content mismatch for {out_name}"
        else:
            dest = workspace / rel
            assert dest.is_file(), f"Expected file {rel}"
            assert dest.read_bytes() == src.read_bytes(), f"Content mismatch for {rel}"


def _canonical_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Stable deep structure for equality after JSON5 save/load."""
    return json.loads(json.dumps(d, sort_keys=True))


def _roundtrip_short_name(role: str) -> str:
    """Unique CLI name per role (matches ``run_add`` / ``run_remove`` slug derivation)."""
    return f"FixtureRoundtrip-{role}"


def _expected_agent_id_after_add(short_name: str) -> str:
    """Same as ``run_add``: optional ``wawa-`` prefix, then ``slugify_agent_id``."""
    display = short_name if short_name.startswith("wawa-") else f"wawa-{short_name}"
    return slugify_agent_id(display)


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


@pytest.mark.parametrize("role", sorted(ROLES_ALLOWED_FOR_MANUAL_ADD))
def test_add_remove_roundtrip_matches_fixture_openclaw_snapshot_per_role(
    tmp_path: Path, role: str
) -> None:
    """For every manually addable role: add agent, workspace matches rendered templates, remove restores config."""
    if not FIXTURE_OPENCLAW_JSON.is_file():
        pytest.skip("fixtures/openclaw/openclaw.json missing")

    role_src = REPO_ROOT / "agents" / role
    assert role_src.is_dir(), f"Repo must ship template for role {role!r}: {role_src}"

    config_path = tmp_path / "openclaw.json"
    state_dir = tmp_path / "openclaw_state"
    shutil.copyfile(FIXTURE_OPENCLAW_JSON, config_path)

    initial = load_config(config_path)
    snapshot = _canonical_dict(initial)

    short_name = _roundtrip_short_name(role)
    expected_id = _expected_agent_id_after_add(short_name)
    display_name = f"wawa-{short_name}"

    add_args = Namespace(
        name=short_name,
        role=role,
        config=config_path,
        state_dir=state_dir,
        repo=REPO_ROOT,
        yes=True,
        wawa_workspace=None,
    )
    assert run_add(add_args) == 0

    after_add = load_config(config_path)
    ids = [a.get("id") for a in after_add["agents"]["list"] if isinstance(a, dict)]
    assert expected_id in ids

    entry = next(
        a for a in after_add["agents"]["list"] if isinstance(a, dict) and a.get("id") == expected_id
    )
    assert entry.get("name") == display_name
    assert "workspace" in entry and "agentDir" in entry

    ws = state_dir / f"workspace-{expected_id}"
    ad = state_dir / "agents" / expected_id / "agent"
    assert ws.is_dir()
    assert (ws / "AGENTS.md").is_file()
    assert ad.is_dir()
    _assert_workspace_matches_rendered_j2(
        ws,
        role=role,
        repo=REPO_ROOT,
        agent_id=expected_id,
        agent_display_name=display_name,
    )
    assert Path(entry["workspace"]).expanduser().resolve() == ws.resolve()
    assert Path(entry["agentDir"]).expanduser().resolve() == ad.resolve()

    remove_args = Namespace(
        name=short_name,
        purge=True,
        yes=True,
        config=config_path,
        state_dir=state_dir,
    )
    assert run_remove(remove_args) == 0

    assert not ws.exists()
    assert not (state_dir / "agents" / expected_id).exists()

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
        yes=True,
        wawa_workspace=None,
    )
    assert run_add(add_args) == 0

    ws_ch = state_dir / "workspace-wawa-chantest"
    _assert_workspace_matches_rendered_j2(
        ws_ch,
        role="designer",
        repo=REPO_ROOT,
        agent_id="wawa-chantest",
        agent_display_name="wawa-ChanTest",
    )

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
