from __future__ import annotations

import json
from pathlib import Path

from wawa_openclaw.cli import run_sync_agents


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_run_sync_agents_rerenders_and_skips_memory(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    role_src = repo / "agents" / "designer"
    role_src.mkdir(parents=True)
    (role_src / "AGENTS.md.j2").write_text("# Agent {{ identity_agent_call_name }}\n", encoding="utf-8")
    (role_src / "HEARTBEAT.md.j2").write_text("# HEARTBEAT {{ role }}\n", encoding="utf-8")
    (role_src / "MEMORY.md.j2").write_text("TEMPLATE MEMORY SHOULD NOT OVERWRITE\n", encoding="utf-8")

    state = tmp_path / "openclaw_state"
    aid = "wawa-designer"
    ws = state / f"workspace-wawa-{aid}"
    ws.mkdir(parents=True)
    (ws / "AGENTS.md").write_text("old agents\n", encoding="utf-8")
    (ws / "HEARTBEAT.md").write_text("old heartbeat\n", encoding="utf-8")
    (ws / "MEMORY.md").write_text("user memory keep me\n", encoding="utf-8")

    cfg_path = tmp_path / "openclaw.json"
    _write_json(
        cfg_path,
        {
            "agents": {
                "defaults": {},
                "list": [
                    {
                        "id": aid,
                        "name": "wawa-designer",
                        "workspace": str(ws),
                    }
                ],
            }
        },
    )

    rc = run_sync_agents(config=cfg_path, state_dir=state, repo=repo)
    assert rc == 0
    assert (ws / "AGENTS.md").read_text(encoding="utf-8").strip() == "# Agent Default Designer"
    assert (ws / "HEARTBEAT.md").read_text(encoding="utf-8").strip() == "# HEARTBEAT designer"
    assert (ws / "MEMORY.md").read_text(encoding="utf-8") == "user memory keep me\n"

