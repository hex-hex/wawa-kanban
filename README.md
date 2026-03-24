# Wawa Kanban

Wawa Kanban is a set of software development agents with a kanban UI and workflow.

## Installation

The usual way to get the app running is the **bootstrap** script below. **Clone the repo** if you want to run from source or work on the code (see [Development](#development)).

### Quick install (bootstrap)

Runs `install.sh` from this repo: installs the `wkanban` bootstrap script and runs `wkanban init`.

Requirements:

- `docker` available and Docker Engine reachable

`wkanban init` starts the Kanban container with your workspace and **`~/.openclaw` mounted into the image** (at `/home/appuser/.openclaw`), then runs `uv run wkanban project add default` and `uv run wkanban agent add-default` **inside the container** so the host does not need Python or `uv`. OpenClaw config and agent state therefore live on the host under `~/.openclaw`, same as before.

```bash
curl -fsSL https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/install.sh | sh
# or
wget -qO- https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/install.sh | sh
```

When it finishes, open http://localhost:5020.

### From source (development)

**Prerequisites**

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (dependencies and running the app)
- Optional: **Node/npm** if you will change styles and regenerate CSS (see [Development](#development))

```bash
git clone https://github.com/hex-hex/wawa-kanban.git
cd wawa-kanban
uv sync
uv run app.py
```

The app listens at http://localhost:5020.

---

## Development

### Workspace and collaboration

- **Fixture workspace (dev/tests only):** `fixtures/workspace` is sample data for local runs and automated tests. It is **not** copied into the Kanban Docker image (`.dockerignore` excludes `fixtures/`). Recreate layout with `wkanban project add` / `wkanban agent add` (or mount your own tree).
- **App default (no env):** when `WAWA_WORKSPACE_PATH` is unset, the app still defaults to `fixtures/workspace` for convenience in a git checkout.
- **Override:** set `WAWA_WORKSPACE_PATH` to a directory that includes `projects/` and `agents/` (same layout as production).
- **Tickets:** markdown files with frontmatter under each project’s column folders (`backlog/`, `implementing/`, etc.) and under agent folders for in-progress work.
- **Agent instructions:** role docs live in this repo under `agents/` (e.g. designer, developer, code-verifier, general-verifier). They describe how agents cooperate on the same workspace.

### CLI: agents and projects

From the repo (after `uv sync`), the **`wkanban`** command groups subcommands (OpenClaw agents today; workspace projects are stubs):

```bash
uv run wkanban agent add "Alex" --role developer
uv run wkanban agent remove "Alex"              # drop from openclaw.json only
uv run wkanban agent remove "Alex" --purge --yes   # also delete workspace + agentDir
uv run wkanban agent list                       # ids from openclaw.json agents.list (sorted)
uv run wkanban agent list --long                # id<TAB>name
uv run wkanban agent list --wawa-only --wawa-workspace ~/.wawa-kanban/workspace   # Wawa-managed only

uv run wkanban project list    # names under workspace projects/ (see --workspace / WAWA_WORKSPACE_PATH)
```

Legacy entry points still work:

```bash
uv run openclaw-agent-add "Alex" --role developer
uv run openclaw-agent-remove "Alex"
```

#### OpenClaw agent helpers

- **Fixture config (dev/tests only):** `fixtures/openclaw/openclaw.json` — minimal empty `agents` tree for local development or tests. **Installers and the Kanban Docker image do not copy this into your real OpenClaw home.** Production and normal installs **must keep** your existing OpenClaw config; mount `~/.openclaw` (or set `OPENCLAW_STATE_DIR`) to that real directory. See `fixtures/openclaw/README.md`. Do not commit real secrets.
- **Config path:** defaults to **`$OPENCLAW_STATE_DIR/openclaw.json`** (JSON5 read/write). Default `OPENCLAW_STATE_DIR` is `~/.openclaw`. Set only **`OPENCLAW_STATE_DIR`** to use a self-contained tree (config + agent state in one directory). Override the config file location with **`OPENCLAW_CONFIG_PATH`** if needed (then it is not required to live under `OPENCLAW_STATE_DIR`).
- **State / workspaces:** under `OPENCLAW_STATE_DIR`. Each `agent add` creates `workspace-wawa-<slug>/` and `agents/<slug>/agent/`, and appends one entry to `agents.list`.
- **Templates:** `--role` is one of `designer`, `developer`, `code-verifier`, `general-verifier`, `lead`, `project-manager` (must match a folder under this repo’s `agents/`). Repo root defaults to the parent of `wawa_openclaw/`; override with `WAWA_KANBAN_ROOT`.

If you use the installed `wkanban` bootstrap script, **`wkanban init` and `wkanban uninstall` do not require a git clone or `uv`**. For other subcommands (`wkanban agent …`, `wkanban project …`, or `wkanban openclaw-*` aliases), set `WAWA_KANBAN_ROOT` to this git clone and install `uv`, then e.g. `wkanban agent add "Alex" --role developer`. The same script accepts `wkanban openclaw-agent-add …` as an alias for `wkanban agent add …`.

**Docker:** the published Kanban image runs as user `appuser` (home `/home/appuser`). `wkanban init` mounts `-v ~/.openclaw:/home/appuser/.openclaw` next to the workspace. For the OpenClaw gateway, mount the same host directory into the gateway container (for example `-v ~/.openclaw:/root/.openclaw` if the gateway runs as root), so agents see the same files as the Kanban app.

### Running with Docker

If you need to **build and run your own image** while developing (e.g. to verify the Dockerfile or run in an isolated environment), from the repo root:

```bash
docker build -t wawa-kanban .
docker run -p 5020:5020 wawa-kanban
```

The image uses Debian Bookworm (slim) with an **empty** workspace at `/app/.workspace` (`projects/` and `agents/` only). Mount your own workspace or populate it via CLI:

```bash
docker run -p 5020:5020 -e WAWA_WORKSPACE_PATH=/data -v /path/to/workspace:/data wawa-kanban
```

### UI styles (UnoCSS)

If you change `cls` classes in Python or Uno config, regenerate CSS:

```bash
npm run build:css    # one-off
npm run dev:css      # watch Python files and rebuild
```

### Tests

```bash
uv sync --extra test
uv run pytest
```

Browser e2e (`tests/e2e/test_modal_open_close.py`) starts a temporary server on port **5022** by default so it does not collide with a dev app on **5021**. Override in either order (**CLI wins over env**):

```bash
uv run pytest tests/e2e/ --wawa-e2e-port=5030
# or
export WAWA_E2E_PORT=5030
uv run pytest tests/e2e/
```

UI assertions belong in **e2e** tests (HTTP against the running app), not in unit tests that render a single component in isolation.
