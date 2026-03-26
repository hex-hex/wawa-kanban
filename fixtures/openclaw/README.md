# OpenClaw fixture config

**Dev and automated tests only.** This file is **not** used by real installs. Wawa does **not** copy `fixtures/openclaw/` into your machine’s OpenClaw home or into production containers. In production you **keep your existing** `openclaw.json` (and the rest of your OpenClaw state); mount that directory or set `OPENCLAW_STATE_DIR` to it.

- **`openclaw.json`** — committed **starter template** for local dev / CI (empty `agents.list`). For a throwaway test tree, copy it to a separate directory (see below). **Do not** overwrite a real `~/.openclaw/openclaw.json` with this file unless you intend to reset that environment. Add secrets only outside the repo; avoid committing real keys.

## One env var: `OPENCLAW_STATE_DIR`

Wawa resolves config like this (`wawa_openclaw/paths.py`):

- If **`OPENCLAW_CONFIG_PATH`** is set → that file is used.
- Else → **`$OPENCLAW_STATE_DIR/openclaw.json`** (default `OPENCLAW_STATE_DIR` is `~/.openclaw`).

So for local or container testing you can point **only** at a directory:

```bash
export OPENCLAW_STATE_DIR="$PWD/fixtures/openclaw-state"
mkdir -p "$OPENCLAW_STATE_DIR"
cp fixtures/openclaw/openclaw.json "$OPENCLAW_STATE_DIR/openclaw.json"
# edit openclaw.json as needed; `wkanban agent add` will create workspace-<agent_id> under OPENCLAW_STATE_DIR (Wawa: workspace-wawa-<role-slug>)
```

## Production / Docker

Mount the host’s real OpenClaw directory (e.g. `~/.openclaw`) into the container and set **`OPENCLAW_STATE_DIR`** to that mount path inside the container so it matches a normal OpenClaw layout (`openclaw.json` + agent dirs in the same tree).
