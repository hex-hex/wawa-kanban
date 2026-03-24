# Wawa Kanban - Debian-based Docker image

# Stage 1: Build CSS with UnoCSS
FROM node:22-bookworm-slim AS css-builder

WORKDIR /build

COPY package.json package-lock.json* ./
RUN npm ci

COPY scripts/build-css.mjs scripts/
COPY uno.config.ts ./
COPY src/ src/
COPY app.py config.py ./

RUN npm run build:css

# Stage 2: Python runtime
FROM python:3.13-slim-bookworm

# Minimal runtime deps; no extra apt packages needed

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml README.md uv.lock* ./
COPY wawa_openclaw/ wawa_openclaw/
RUN uv sync --frozen --no-dev

COPY . .
COPY --from=css-builder /build/static/uno.css static/uno.css

# Empty runtime workspace (fixtures/ is excluded from the image; populate via volume or wkanban project/agent commands).
RUN mkdir -p /app/.workspace/projects /app/.workspace/agents

# Home for OpenClaw mount (~/.openclaw -> /home/appuser/.openclaw); entrypoint aligns UID/GID.
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV WAWA_WORKSPACE_PATH=/app/.workspace

EXPOSE 5020

# Starts as root; docker-entrypoint.sh chowns /app (and mounts if present) then drops to PUID:PGID.
ENTRYPOINT ["/docker-entrypoint.sh"]
# Override workspace: mount your own tree at /app/.workspace or set WAWA_WORKSPACE_PATH.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5020"]
