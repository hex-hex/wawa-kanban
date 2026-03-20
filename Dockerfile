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

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5020

# Use bundled fixtures/workspace by default. Override:
#   docker run -e WAWA_WORKSPACE_PATH=/data -v /host/workspace:/data ...
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5020"]
