# Wawa Kanban

Wawa Kanban is a set of software development agents with a kanban UI and workflow.

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (dependencies and running the app)
- Optional: **Node/npm** if you will change styles and regenerate CSS (see [Development](#development))

### From source (clone and sync)

```bash
git clone https://github.com/hex-hex/wawa-kanban.git
cd wawa-kanban
uv sync
```

Start the app:

```bash
uv run app.py
```

The app listens at http://localhost:5020.

### Docker

Build and run:

```bash
docker build -t wawa-kanban .
docker run -p 5020:5020 wawa-kanban
```

The image uses Debian Bookworm (slim) and the bundled `fixtures/workspace` by default. Use your own workspace:

```bash
docker run -p 5020:5020 -e WAWA_WORKSPACE_PATH=/data -v /path/to/workspace:/data wawa-kanban
```

### Bootstrap (one-shot installer)

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

---

## Development

### Workspace and collaboration

- **Default workspace:** `fixtures/workspace` (contains `projects/` and `agents/`). Tests and local dev use it unless you override.
- **Override:** set `WAWA_WORKSPACE_PATH` to a directory that includes `projects/` and `agents/` (same layout as the fixture).
- **Tickets:** markdown files with frontmatter under each project’s column folders (`backlog/`, `implementing/`, etc.) and under agent folders for in-progress work.
- **Agent instructions:** role docs live in this repo under `agents/` (e.g. designer, developer, verifier). They describe how agents cooperate on the same workspace.

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

UI assertions belong in **e2e** tests (HTTP against the running app), not in unit tests that render a single component in isolation.
