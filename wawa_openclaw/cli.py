from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wawa_openclaw.agents_ops import (
    ALLOWED_ROLES,
    ROLES_ALLOWED_FOR_MANUAL_ADD,
    ROLES_DISALLOWED_FOR_MANUAL_ADD,
    agent_id_in_config,
    agent_workspace_state_path,
    ensure_kanban_slot_dir,
    find_wawa_agents_by_state,
    kanban_slot_from_agent_id,
    materialize_agent,
    merge_agent_into_config,
    plan_add_agent,
    purge_agent_paths,
    remove_agent_from_config,
    slugify_agent_id,
    sync_agent_guidance_files,
)
from wawa_openclaw.config_io import ensure_agents_tree, load_config, save_config
from wawa_openclaw.paths import openclaw_config_path, openclaw_state_dir, repo_root


def add_agent_add_arguments(p: argparse.ArgumentParser) -> None:
    """Register OpenClaw agent-add CLI arguments on an existing parser (for nested wkanban CLI)."""
    p.add_argument("name", help="Display name; used to derive agent id (slug).")
    p.add_argument(
        "--role",
        required=True,
        choices=sorted(ROLES_ALLOWED_FOR_MANUAL_ADD),
        help="Template folder under agents/ in the Wawa Kanban repo (lead and project-manager are init-only).",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Skip Proceed? [Y/n] prompt (required when stdin is not a TTY).",
    )
    p.add_argument(
        "--wawa-workspace",
        type=Path,
        default=None,
        metavar="DIR",
        help="After add, create Kanban slot directory agents/<plural>/<slot>/ under this workspace root.",
    )


def _parser_add() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Register a new OpenClaw agent: append to openclaw.json, create workspace and agentDir, "
            "and render role templates from this repo's agents/<role>/ (*.md.j2 -> *.md)."
        )
    )
    add_agent_add_arguments(p)
    return p


def add_agent_remove_arguments(p: argparse.ArgumentParser) -> None:
    """Register OpenClaw agent-remove CLI arguments on an existing parser (for nested wkanban CLI)."""
    p.add_argument("name", help="Same name as used for add; id is derived by slug.")
    p.add_argument(
        "--purge",
        action="store_true",
        help="Delete ~/.openclaw/workspace-<id> and ~/.openclaw/agents/<id>/ after removing from config.",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="With --purge, skip confirmation.",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )


def _parser_remove() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Remove an agent created by wkanban agent add from openclaw.json (and optional disk purge)."
    )
    add_agent_remove_arguments(p)
    return p


def _confirm_proceed_add(*, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        return False
    try:
        reply = input("Proceed? [Y/n]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("", "y", "yes")


def _confirm_init_batch(*, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        return False
    try:
        reply = input("Register missing wawa-<role> agents (one per role)? [Y/n]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("", "y", "yes")


def run_add(args: argparse.Namespace) -> int:
    """Execute agent add from a parsed argparse Namespace (shared by main_add and wawa_cli)."""
    try:
        if args.role in ROLES_DISALLOWED_FOR_MANUAL_ADD:
            print(
                f"Error: Role {args.role!r} cannot be added with agent add; "
                f"use init (wawa-{args.role}) to register the single default instance.",
                file=sys.stderr,
            )
            return 1

        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        root = args.repo or repo_root()

        name = args.name if args.name.startswith("wawa-") else f"wawa-{args.name}"
        agent_id = slugify_agent_id(name)

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)

        if agent_id_in_config(cfg, agent_id):
            print(
                f"Error: Agent id {agent_id!r} already exists in openclaw.json. Refusing to create.",
                file=sys.stderr,
            )
            return 1

        entry, workspace, agent_dir, role_src = plan_add_agent(
            name=name, role=args.role, root=root, state=state
        )

        assume_yes = bool(getattr(args, "yes", False))
        if not assume_yes and not sys.stdin.isatty():
            print(
                "Error: stdin is not a TTY; pass --yes to create the agent without a prompt.",
                file=sys.stderr,
            )
            return 1

        summary = (
            f"Add agent: name={name!r} role={args.role!r} id={entry['id']!r}\n"
            f"  workspace: {workspace}\n"
            f"  agentDir:  {agent_dir}"
        )
        print(summary)
        if not _confirm_proceed_add(assume_yes=assume_yes):
            print("Aborted.", file=sys.stderr)
            return 1

        merge_agent_into_config(cfg, entry)
        save_config(config_path, cfg)
        materialize_agent(
            workspace=workspace,
            agent_dir=agent_dir,
            role_src=role_src,
            agent_id=entry["id"],
            agent_display_name=entry["name"],
            role=args.role,
        )

        wawa_ws = getattr(args, "wawa_workspace", None)
        if wawa_ws is not None:
            ensure_kanban_slot_dir(
                Path(wawa_ws), args.role, kanban_slot_from_agent_id(entry["id"])
            )

        print(f"Added agent name={name!r} id={entry['id']!r}")
        print(f"  workspace: {workspace}")
        print(f"  agentDir:  {agent_dir}")
        print(f"  config:    {config_path}")
        print(
            "Mount this OpenClaw home in Docker, e.g. -v ~/.openclaw:/root/.openclaw "
            "(adjust user path inside the container)."
        )
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main_add(argv: list[str] | None = None) -> int:
    args = _parser_add().parse_args(argv)
    return run_add(args)


def run_remove(args: argparse.Namespace) -> int:
    """Execute agent remove from a parsed argparse Namespace (shared by main_remove and wawa_cli)."""
    try:
        config_path = args.config or openclaw_config_path()
        state = args.state_dir or openclaw_state_dir()
        # Match run_add: same display name → same derived id (wawa- prefix when omitted).
        display_name = args.name if args.name.startswith("wawa-") else f"wawa-{args.name}"
        agent_id = slugify_agent_id(display_name)

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)
        remove_agent_from_config(cfg, agent_id)
        save_config(config_path, cfg)
        print(f"Removed agent id={agent_id!r} from {config_path}")

        if args.purge:
            if not args.yes:
                ws = agent_workspace_state_path(state, agent_id)
                ar = state / "agents" / agent_id
                print(f"Will delete:\n  {ws}\n  {ar}")
                confirm = input("Type yes to delete: ").strip().lower()
                if confirm != "yes":
                    print("Aborted; config updated but files kept.")
                    return 0
            purge_agent_paths(agent_id, state=state)
            print("Purged workspace and agentDir.")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main_remove(argv: list[str] | None = None) -> int:
    args = _parser_remove().parse_args(argv)
    return run_remove(args)


def _parser_init_agents() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Register all default Wawa agents (one per role) into openclaw.json. "
            "Each agent is named 'wawa-<role>'. Already-registered agents are skipped."
        )
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Skip batch Proceed? [Y/n] prompt (required when stdin is not a TTY).",
    )
    return p


def run_init_agents(
    *,
    config: Path | None = None,
    state_dir: Path | None = None,
    repo: Path | None = None,
    yes: bool = False,
) -> int:
    """Register all default Wawa agents (one per role)."""
    config_path = config or openclaw_config_path()
    state = state_dir or openclaw_state_dir()
    root = repo or repo_root()

    cfg = load_config(config_path)
    ensure_agents_tree(cfg)

    if not yes and not sys.stdin.isatty():
        print(
            "Error: stdin is not a TTY; pass --yes to register default agents without a prompt.",
            file=sys.stderr,
        )
        return 1
    if not _confirm_init_batch(assume_yes=yes):
        print("Aborted.", file=sys.stderr)
        return 1

    errors = 0
    for role in sorted(ALLOWED_ROLES):
        name = f"wawa-{role}"
        try:
            entry, workspace, agent_dir, role_src = plan_add_agent(
                name=name, role=role, root=root, state=state
            )
            merge_agent_into_config(cfg, entry)
            save_config(config_path, cfg)
            materialize_agent(
                workspace=workspace,
                agent_dir=agent_dir,
                role_src=role_src,
                agent_id=entry["id"],
                agent_display_name=entry["name"],
                role=role,
            )
            print(f"  [added]   {name} (role={role})")
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                print(f"  [skipped] {name} (already registered)")
            else:
                print(f"  [error]   {name}: {msg}", file=sys.stderr)
                errors += 1

    print(f"Done. Config: {config_path}")
    return 1 if errors else 0


def main_init_agents(argv: list[str] | None = None) -> int:
    args = _parser_init_agents().parse_args(argv)
    return run_init_agents(
        config=args.config,
        state_dir=args.state_dir,
        repo=args.repo,
        yes=args.yes,
    )


def _parser_uninstall_agents() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Remove all Wawa-managed agents from openclaw.json. "
            "Strict ownership model: only agents whose id starts with 'wawa-' AND whose "
            "workspace equals state_dir/workspace-<id> are removed."
        )
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    return p


def main_uninstall_agents(argv: list[str] | None = None) -> int:
    args = _parser_uninstall_agents().parse_args(argv)
    return run_uninstall_agents(config=args.config, state_dir=args.state_dir)


def run_uninstall_agents(
    *,
    config: Path | None = None,
    state_dir: Path | None = None,
) -> int:
    config_path = config or openclaw_config_path()
    state = state_dir or openclaw_state_dir()

    cfg = load_config(config_path)
    if not cfg:
        print("No openclaw.json found, nothing to clean up.")
        return 0

    agent_ids = find_wawa_agents_by_state(cfg, state)
    if not agent_ids:
        print("No Wawa-managed agents found in openclaw.json.")
        return 0

    for agent_id in agent_ids:
        remove_agent_from_config(cfg, agent_id, allow_protected_removal=True)
        purge_agent_paths(agent_id, state=state, allow_protected_removal=True)
        print(f"  [removed] {agent_id}")

    save_config(config_path, cfg)
    print(f"Done. Removed {len(agent_ids)} agent(s) from {config_path}")
    return 0


def _parser_uninstall_analyze() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Analyze potential uninstall residuals before deleting Wawa agents. "
            "Exit code 0 means safe; exit code 3 means possible residuals (uninstall would "
            "not remove some mismatched agents or orphan state dirs)."
        )
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    return p


def main_uninstall_analyze(argv: list[str] | None = None) -> int:
    args = _parser_uninstall_analyze().parse_args(argv)
    return run_uninstall_analyze(config=args.config, state_dir=args.state_dir)


def run_uninstall_analyze(
    *,
    config: Path | None = None,
    state_dir: Path | None = None,
) -> int:
    """Exit code contract for shell wrapper:
    - 0: no possible residual detected
    - 3: warnings (possible residual detected)
    - 1: analysis failed (invalid paths/config)
    """
    try:
        config_path = config or openclaw_config_path()
        state = state_dir or openclaw_state_dir()

        cfg = load_config(config_path)
        ensure_agents_tree(cfg)

        strict_ids = set(find_wawa_agents_by_state(cfg, state))

        cfg_wawa_ids: list[str] = []
        for a in cfg.get("agents", {}).get("list", []):
            if isinstance(a, dict):
                aid = a.get("id")
                if isinstance(aid, str) and aid.startswith("wawa-"):
                    cfg_wawa_ids.append(aid)

        mismatched_ids = sorted(set(cfg_wawa_ids) - strict_ids)

        orphan_workspaces: list[str] = []
        orphan_agent_dirs: list[str] = []

        if state.is_dir():
            ws_prefix = "workspace-"
            for item in state.iterdir():
                if not item.is_dir():
                    continue
                if not item.name.startswith(ws_prefix):
                    continue
                agent_id = item.name[len(ws_prefix) :]
                if agent_id.startswith("wawa-") and agent_id not in strict_ids:
                    orphan_workspaces.append(agent_id)

            agents_root = state / "agents"
            if agents_root.is_dir():
                for d in agents_root.iterdir():
                    if d.is_dir() and d.name.startswith("wawa-") and d.name not in strict_ids:
                        orphan_agent_dirs.append(d.name)

        warnings: list[str] = []
        if mismatched_ids:
            warnings.append(
                "openclaw.json has Wawa agents but strict-state match failed for these ids "
                "(uninstall will NOT remove them): "
                + ", ".join(mismatched_ids)
            )
        if orphan_workspaces or orphan_agent_dirs:
            parts: list[str] = []
            if orphan_workspaces:
                parts.append("orphan workspaces: " + ", ".join(sorted(set(orphan_workspaces))))
            if orphan_agent_dirs:
                parts.append("orphan agent dirs: " + ", ".join(sorted(set(orphan_agent_dirs))))
            warnings.append("OpenClaw state contains files uninstall would not purge: " + " ; ".join(parts))

        if warnings:
            for w in warnings:
                print(f"WARNING: {w}", file=sys.stderr)
            print("Possible residual detected. Use --force to proceed.", file=sys.stderr)
            return 3

        print("OK: no possible residual detected.", file=sys.stderr)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _parser_sync_agents() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Re-render guidance files for existing Wawa agents from latest role templates. "
            "Only *.md.j2 template outputs are rendered; MEMORY*.md files are never overwritten."
        )
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to openclaw.json (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json).",
    )
    p.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="OpenClaw state dir (default: OPENCLAW_STATE_DIR or ~/.openclaw).",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Wawa Kanban repo root (default: WAWA_KANBAN_ROOT or parent of wawa_openclaw).",
    )
    return p


def _role_for_agent_entry(agent: dict, agent_id: str) -> str | None:
    role = agent.get("role")
    if isinstance(role, str) and role in ALLOWED_ROLES:
        return role
    for candidate in sorted(ALLOWED_ROLES):
        if agent_id == slugify_agent_id(f"wawa-{candidate}"):
            return candidate
    return None


def _workspace_dir_for_sync(state: Path, agent_id: str, ws_raw: object) -> Path:
    """Resolve agent workspace directory for sync.

    If ``openclaw.json`` stores an absolute path from another machine or user (for example,
    ``/home/<user>/.openclaw/...``) but sync runs inside Docker with a different ``HOME``,
    that path does not exist in the container. Fall back to
    :func:`~wawa_openclaw.agents_ops.agent_workspace_state_path` under the current
    ``--state-dir``.
    """
    canonical = agent_workspace_state_path(state, agent_id)
    if isinstance(ws_raw, str) and ws_raw.strip():
        stored = Path(ws_raw).expanduser().resolve()
        if stored.is_dir():
            return stored
        return canonical
    return canonical


def run_sync_agents(
    *,
    config: Path | None = None,
    state_dir: Path | None = None,
    repo: Path | None = None,
) -> int:
    config_path = config or openclaw_config_path()
    state = state_dir or openclaw_state_dir()
    root = repo or repo_root()

    cfg = load_config(config_path)
    ensure_agents_tree(cfg)

    synced = 0
    skipped = 0
    errors = 0
    for agent in cfg.get("agents", {}).get("list", []):
        if not isinstance(agent, dict):
            continue
        aid = agent.get("id")
        if not isinstance(aid, str) or not aid.startswith("wawa-"):
            continue
        role = _role_for_agent_entry(agent, aid)
        if role is None:
            print(f"  [skipped] {aid} (cannot determine role; missing entry.role and not a default role id)")
            skipped += 1
            continue

        workspace = _workspace_dir_for_sync(state, aid, agent.get("workspace"))
        role_src = root / "agents" / role
        display_name = agent.get("name") if isinstance(agent.get("name"), str) and agent.get("name") else aid
        try:
            rendered = sync_agent_guidance_files(
                workspace=workspace,
                role_src=role_src,
                agent_id=aid,
                agent_display_name=display_name,
                role=role,
            )
            print(f"  [synced]  {aid} (role={role}, files={rendered})")
            synced += 1
        except ValueError as e:
            print(f"  [error]   {aid}: {e}", file=sys.stderr)
            errors += 1

    print(f"Done. synced={synced} skipped={skipped} errors={errors}")
    return 1 if errors else 0


def main_sync_agents(argv: list[str] | None = None) -> int:
    args = _parser_sync_agents().parse_args(argv)
    return run_sync_agents(
        config=args.config,
        state_dir=args.state_dir,
        repo=args.repo,
    )


def main() -> int:
    print(
        "Use: wkanban agent add|remove|list|add-default|sync|analyze-uninstall|uninstall-all.",
        file=sys.stderr,
    )
    return 2
