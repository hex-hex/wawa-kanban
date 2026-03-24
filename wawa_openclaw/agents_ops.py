from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment

from wawa_openclaw.paths import openclaw_state_dir, repo_root, to_config_path

ALLOWED_ROLES = frozenset(
    {
        "designer",
        "developer",
        "info-officer",
        "code-verifier",
        "general-verifier",
        "lead",
        "project-manager",
    }
)

# OpenClaw role -> Kanban workspace/agents/<plural>/<kanban_slot>/ (None = no ticket queue)
KANBAN_PLURAL_BY_ROLE: dict[str, str | None] = {
    "developer": "developers",
    "designer": "designers",
    "info-officer": "info-officers",
    "code-verifier": "code-verifiers",
    "general-verifier": "general-verifiers",
    "lead": None,
    "project-manager": None,
}

_SLUG = re.compile(r"[^a-z0-9-]+")


def slugify_agent_id(name: str) -> str:
    s = name.strip().lower().replace("_", "-")
    s = _SLUG.sub("-", s).strip("-")
    if not s:
        raise ValueError("Name must yield a non-empty agent id (use letters, digits, or hyphen).")
    return s


def kanban_slot_from_agent_id(agent_id: str) -> str:
    """Directory name under workspace/agents/<plural>/ (no wawa- prefix)."""
    if agent_id.startswith("wawa-"):
        rest = agent_id[5:]
        return rest if rest else agent_id
    return agent_id


def identity_display_name_from(agent_display_name: str) -> str:
    """Strip one leading ``wawa-`` (case-sensitive) for human-facing IDENTITY text."""
    s = agent_display_name.strip()
    if s.startswith("wawa-"):
        rest = s[5:]
        return rest if rest else s
    return s


def build_agent_template_context(
    *,
    agent_id: str,
    agent_display_name: str,
    role: str,
) -> dict[str, Any]:
    """Variables for ``*.md.j2`` when materializing an OpenClaw agent workspace."""
    kanban_slot = kanban_slot_from_agent_id(agent_id)
    identity_name = identity_display_name_from(agent_display_name)
    plural = KANBAN_PLURAL_BY_ROLE.get(role)
    ticket_folder = (
        f"workspace/agents/{plural}/{kanban_slot}/" if plural else ""
    )
    return {
        "agent_id": agent_id,
        "agent_display_name": agent_display_name,
        "identity_display_name": identity_name,
        "kanban_slot": kanban_slot,
        "role": role,
        "kanban_agents_base": "workspace/agents",
        "kanban_type_folder": plural or "",
        "kanban_ticket_folder": ticket_folder,
    }


def agent_id_in_config(cfg: dict[str, Any], agent_id: str) -> bool:
    lst = cfg.get("agents", {}).get("list", [])
    if not isinstance(lst, list):
        return False
    return any(isinstance(a, dict) and a.get("id") == agent_id for a in lst)


_jinja_env = Environment(autoescape=False)


def _materialize_role_tree(
    role_src: Path,
    dest_root: Path,
    context: dict[str, Any],
) -> None:
    """Copy or render templates under ``role_src`` into ``dest_root`` (recursive)."""
    dest_root.mkdir(parents=True, exist_ok=True)
    for item in sorted(role_src.iterdir()):
        if item.name.startswith("."):
            continue
        rel_name = item.name
        if item.is_file():
            if rel_name.endswith(".md.j2"):
                out_name = rel_name[:-3]  # strip .j2 -> .md
                text = item.read_text(encoding="utf-8")
                rendered = _jinja_env.from_string(text).render(**context)
                (dest_root / out_name).write_text(rendered, encoding="utf-8")
            else:
                shutil.copy2(item, dest_root / rel_name)
        elif item.is_dir():
            _materialize_role_tree(item, dest_root / rel_name, context)


def plan_add_agent(
    *,
    name: str,
    role: str,
    root: Path | None = None,
    state: Path | None = None,
) -> tuple[dict[str, Any], Path, Path, Path]:
    """Validate paths and build config entry; does not create files on disk."""
    if role not in ALLOWED_ROLES:
        raise ValueError(
            f"Unknown role {role!r}. Expected one of: {', '.join(sorted(ALLOWED_ROLES))}"
        )
    root = root or repo_root()
    state = state or openclaw_state_dir()
    role_src = root / "agents" / role
    if not role_src.is_dir():
        raise ValueError(f"Role template directory missing: {role_src}")

    agent_id = slugify_agent_id(name)
    workspace = state / f"workspace-wawa-{agent_id}"
    agent_dir = state / "agents" / agent_id / "agent"
    agent_root = state / "agents" / agent_id

    if agent_root.exists():
        raise ValueError(
            f"OpenClaw agent state already exists: {agent_root}. "
            "Remove the agent first or pick another name."
        )
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError(
            f"Workspace already exists and is not empty: {workspace}. "
            "Remove the agent first or pick another name."
        )

    entry: dict[str, Any] = {
        "id": agent_id,
        "name": name.strip(),
        "workspace": to_config_path(workspace),
        "agentDir": to_config_path(agent_dir),
    }
    return entry, workspace, agent_dir, role_src


def materialize_agent(
    *,
    workspace: Path,
    agent_dir: Path,
    role_src: Path,
    agent_id: str,
    agent_display_name: str,
    role: str,
) -> None:
    """Create agentDir and render ``*.md.j2`` templates into workspace ``*.md``."""
    agent_dir.parent.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)
    ctx = build_agent_template_context(
        agent_id=agent_id,
        agent_display_name=agent_display_name,
        role=role,
    )
    _materialize_role_tree(role_src, workspace, ctx)


def merge_agent_into_config(cfg: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    lst = cfg["agents"]["list"]
    if any(isinstance(a, dict) and a.get("id") == entry["id"] for a in lst):
        raise ValueError(f"Agent id already in openclaw.json: {entry['id']}")
    lst.append(entry)
    return cfg


def remove_agent_from_config(cfg: dict[str, Any], agent_id: str) -> dict[str, Any]:
    """Remove agent from ``agents.list``, strip matching ``bindings``, and drop related channel accounts.

    Channel cleanup (OpenClaw-style):
    - For each removed binding with ``match.channel`` + ``match.accountId``, delete
      ``channels.<channel>.accounts.<accountId>`` when present.
    - Also delete ``channels.*.accounts.<agent_id>`` when the account key equals the agent id
      (e.g. Telegram account id matches agent id).
    """
    lst = cfg["agents"]["list"]
    if not any(isinstance(a, dict) and a.get("id") == agent_id for a in lst):
        raise ValueError(f"No agent with id {agent_id!r} in agents.list")

    accounts_to_drop: list[tuple[str, str]] = []
    bindings = cfg.get("bindings")
    if isinstance(bindings, list):
        new_bindings: list[Any] = []
        for b in bindings:
            if isinstance(b, dict) and b.get("agentId") == agent_id:
                m = b.get("match")
                if isinstance(m, dict):
                    ch = m.get("channel")
                    aid = m.get("accountId")
                    if isinstance(ch, str) and isinstance(aid, str):
                        accounts_to_drop.append((ch, aid))
                continue
            new_bindings.append(b)
        cfg["bindings"] = new_bindings

    cfg["agents"]["list"] = [a for a in lst if not (isinstance(a, dict) and a.get("id") == agent_id)]

    channels = cfg.get("channels")
    if isinstance(channels, dict):
        for ch_name, acc_id in accounts_to_drop:
            ch_val = channels.get(ch_name)
            if isinstance(ch_val, dict):
                acc = ch_val.get("accounts")
                if isinstance(acc, dict) and acc_id in acc:
                    del acc[acc_id]
        for _ch_name, ch_val in channels.items():
            if isinstance(ch_val, dict):
                acc = ch_val.get("accounts")
                if isinstance(acc, dict) and agent_id in acc:
                    del acc[agent_id]

    return cfg


def purge_agent_paths(agent_id: str, state: Path | None = None) -> None:
    state = state or openclaw_state_dir()
    workspace = state / f"workspace-wawa-{agent_id}"
    agent_tree = state / "agents" / agent_id
    if workspace.is_dir():
        shutil.rmtree(workspace)
    if agent_tree.is_dir():
        shutil.rmtree(agent_tree)


def ensure_kanban_slot_dir(workspace_root: Path, role: str, kanban_slot: str) -> None:
    """Create ``<workspace>/agents/<plural>/<kanban_slot>/`` for queue roles only."""
    plural = KANBAN_PLURAL_BY_ROLE.get(role)
    if not plural:
        return
    slot = workspace_root.expanduser().resolve() / "agents" / plural / kanban_slot
    slot.mkdir(parents=True, exist_ok=True)


def find_wawa_agents(cfg: dict[str, Any], wawa_workspace_dir: Path) -> list[str]:
    """Return agent IDs that pass both cross-validation criteria:
    1. id starts with 'wawa-'
    2. workspace path is under wawa_workspace_dir
    """
    wawa_workspace_dir = wawa_workspace_dir.expanduser().resolve()
    result = []
    for agent in cfg.get("agents", {}).get("list", []):
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get("id", "")
        if not agent_id.startswith("wawa-"):
            continue
        raw_ws = agent.get("workspace", "")
        ws_path = Path(raw_ws).expanduser().resolve()
        try:
            ws_path.relative_to(wawa_workspace_dir)
            result.append(agent_id)
        except ValueError:
            pass
    return result
