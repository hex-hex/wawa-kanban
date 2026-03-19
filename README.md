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
- **Agent instructions:** role docs live in this repo under `agents/` (e.g. designer, developer, verifier). They describe how agents cooperate on the same workspace.

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

UI assertions belong in **e2e** tests (HTTP against the running app), not in unit tests that render a single component in isolation.
