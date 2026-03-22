# Wawa Kanban

Wawa Kanban is a set of software development agents with a kanban UI and workflow.

## Installation

The usual way to get the app running is the **bootstrap** script below. **Clone the repo** if you want to run from source or work on the code (see [Development](#development)).

### Quick install (bootstrap)

Runs `install.sh` from this repo: installs the `wkanban` bootstrap script and runs `wkanban init`.

Requirements:

- `docker` available and Docker Engine reachable
- `openclaw` on your `PATH`

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

- **Default workspace:** `fixtures/workspace` (contains `projects/` and `agents/`). Tests and local dev use it unless you override.
- **Override:** set `WAWA_WORKSPACE_PATH` to a directory that includes `projects/` and `agents/` (same layout as the fixture).
- **Tickets:** markdown files with frontmatter under each project’s column folders (`backlog/`, `implementing/`, etc.) and under agent folders for in-progress work.
- **Agent instructions:** role docs live in this repo under `agents/` (e.g. designer, developer, code-verifier, general-verifier). They describe how agents cooperate on the same workspace.

### CLI: agents and projects

From the repo (after `uv sync`), the **`wkanban`** command groups subcommands (OpenClaw agents today; workspace projects are stubs):

```bash
uv run wkanban agent add "Alex" --role developer
uv run wkanban agent remove "Alex"              # drop from openclaw.json only
uv run wkanban agent remove "Alex" --purge --yes   # also delete workspace + agentDir

uv run wkanban project list    # not implemented yet (placeholder)
```

Legacy entry points still work:

```bash
uv run openclaw-agent-add "Alex" --role developer
uv run openclaw-agent-remove "Alex"
```

#### OpenClaw agent helpers

- **Config:** `~/.openclaw/openclaw.json` (JSON5 read/write). Override with `OPENCLAW_CONFIG_PATH`.
- **State / workspaces:** under `~/.openclaw/` unless `OPENCLAW_STATE_DIR` is set. Each add creates `workspace-wawa-<slug>/` and `agents/<slug>/agent/`, and appends one entry to `agents.list`.
- **Templates:** `--role` is one of `designer`, `developer`, `code-verifier`, `general-verifier`, `lead`, `project-manager` (must match a folder under this repo’s `agents/`). Repo root defaults to the parent of `wawa_openclaw/`; override with `WAWA_KANBAN_ROOT`.

If you use the installed `wkanban` bootstrap script, set `WAWA_KANBAN_ROOT` to this git clone and run e.g. `wkanban agent add "Alex" --role developer`. The same script still accepts `wkanban openclaw-agent-add …` as an alias for `wkanban agent add …`.

**Docker:** run the OpenClaw gateway container with the host OpenClaw directory mounted (adjust in-container user home if needed), for example `-v ~/.openclaw:/root/.openclaw`, so the new workspace paths stay on the host.

### Running with Docker

If you need to **build and run your own image** while developing (e.g. to verify the Dockerfile or run in an isolated environment), from the repo root:

```bash
docker build -t wawa-kanban .
docker run -p 5020:5020 wawa-kanban
```

The image uses Debian Bookworm (slim) and the bundled `fixtures/workspace` by default. Mount a custom workspace:

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
