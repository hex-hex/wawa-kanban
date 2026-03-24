# Fixtures (development and tests only)

Everything under `fixtures/` is for **local development**, **documentation**, and **automated tests**. It is **not** baked into the Kanban Docker image (see `.dockerignore`).

- **`fixtures/workspace/`** — sample Kanban `projects/` + `agents/` tree. Use `WAWA_WORKSPACE_PATH` in tests or when hacking locally; production-like setups should use `wkanban project add` / `wkanban agent add` or a mounted workspace.
- **`fixtures/openclaw/`** — starter OpenClaw JSON for dev/tests; see `fixtures/openclaw/README.md`.
