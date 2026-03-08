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

The image uses Debian Bookworm (slim). Use the bundled `fixtures/workspace` by default. Override with your own workspace:

```bash
docker run -p 5020:5020 -e WAWA_WORKSPACE_PATH=/data -v /path/to/workspace:/data wawa-kanban
```

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

Tasks and specs live under `workspace/agents/`, organized by role (e.g. designers, developers, testers), for agents to read and update.
