# Wawa Kanban

Wawa Kanban is a set of software development agents with a kanban UI and workflow.

## How to run

**Start the app**

```bash
uv run app.py
```

The app runs at http://localhost:5020.

**Docker**

Build and run with Docker:

```bash
docker build -t wawa-kanban .
docker run -p 5020:5020 wawa-kanban
```

The image uses Debian Bookworm (slim). Inside the container the app uses **`/app/.workspace`** by default (`WAWA_WORKSPACE_PATH=/app/.workspace`), seeded at build time from the repo template. Use your own workspace:

```bash
docker run -p 5020:5020 -v /path/to/your/workspace:/app/.workspace wawa-kanban
```

Or point at another mount path:

```bash
docker run -p 5020:5020 -e WAWA_WORKSPACE_PATH=/data -v /path/to/workspace:/data wawa-kanban
```

**Bootstrap (one-shot install)**

This runs `install.sh` directly from GitHub raw, which installs the `wkanban` bootstrap script and then runs `wkanban init`.

Prerequisites:
- `docker` must be available and Docker Engine must be reachable
- `openclaw` must be available in your `PATH`

```bash
curl -fsSL https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/install.sh | sh
# or
wget -qO- https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/install.sh | sh
```

After it finishes, open http://localhost:5020.

**Frontend styles (optional)**

To change styles and regenerate CSS:

```bash
npm run build:css    # one-off build
npm run dev:css      # watch and rebuild on Python file changes
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependencies and running
- Optional (tests): `uv sync --extra test` then `uv run pytest`

## Agents

Tasks and specs live under `workspace/agents/`, organized by role (e.g. designers, developers, verifiers), for agents to read and update.
