from __future__ import annotations

import json
from pathlib import Path

import pytest

from wawa_openclaw.cli import main_uninstall_analyze


def _write_openclaw_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_uninstall_analyze_ok_strict_match(tmp_path: Path) -> None:
    state = tmp_path / "openclaw_state"
    state.mkdir(parents=True)

    agent_id = "wawa-inside"
    ws = state / f"workspace-{agent_id}"
    ws.mkdir(parents=True)
    (state / "agents" / agent_id).mkdir(parents=True)

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_json(
        cfg,
        {
            "agents": {
                "defaults": {},
                "list": [
                    {"id": agent_id, "name": "Inside", "workspace": str(ws)},
                ],
            }
        },
    )

    rc = main_uninstall_analyze(["--config", str(cfg), "--state-dir", str(state)])
    assert rc == 0


def test_uninstall_analyze_warn_on_workspace_mismatch(tmp_path: Path) -> None:
    state = tmp_path / "openclaw_state"
    state.mkdir(parents=True)

    agent_id = "wawa-mismatch"
    ws_expected = state / f"workspace-{agent_id}"
    ws_expected.mkdir(parents=True)

    # Mismatched workspace path in openclaw.json
    ws_wrong = tmp_path / "legacy" / "workspace-wawa-wawa-mismatch"
    ws_wrong.mkdir(parents=True)

    cfg = tmp_path / "openclaw.json"
    _write_openclaw_json(
        cfg,
        {
            "agents": {
                "defaults": {},
                "list": [
                    {"id": agent_id, "name": "Mismatch", "workspace": str(ws_wrong)},
                ],
            }
        },
    )

    rc = main_uninstall_analyze(["--config", str(cfg), "--state-dir", str(state)])
    assert rc == 3


def test_uninstall_analyze_warn_on_orphan_state(tmp_path: Path) -> None:
    state = tmp_path / "openclaw_state"
    state.mkdir(parents=True)

    agent_id = "wawa-orphan"
    ws = state / f"workspace-{agent_id}"
    ws.mkdir(parents=True)
    (state / "agents" / agent_id).mkdir(parents=True)

    # No agents.list entries in config → strict set empty, state dirs become orphans
    cfg = tmp_path / "openclaw.json"
    _write_openclaw_json(cfg, {"agents": {"defaults": {}, "list": []}})

    rc = main_uninstall_analyze(["--config", str(cfg), "--state-dir", str(state)])
    assert rc == 3

