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

# Seed runtime workspace at /app/.workspace (not fixtures/ in production use).
RUN mkdir -p /app/.workspace && cp -a /app/fixtures/workspace/. /app/.workspace/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV WAWA_WORKSPACE_PATH=/app/.workspace

EXPOSE 5020

# Override workspace: mount your own tree at /app/.workspace or set WAWA_WORKSPACE_PATH.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5020"]
