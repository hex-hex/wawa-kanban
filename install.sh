#!/usr/bin/env sh
set -eu

log() {
  echo "[install] $*"
}

die() {
  echo "[install][ERROR] $*" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

require_cmd() {
  if ! have_cmd "$1"; then
    die "Command not found: $1. Please install it and make sure it is available in your PATH."
  fi
}

# Resolve repo root (directory where this script lives)
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT="$SCRIPT_DIR"
FIXTURES_WS="$REPO_ROOT/fixtures/workspace"

WORKSPACE_DIR="${HOME}/.wawa-kanban/workspace"

IMAGE="wawaassistant/wawa-kanban:latest"
CONTAINER_NAME="wawa-kanban"
PORT="5020"

require_cmd docker
if ! docker info >/dev/null 2>&1; then
  die "Docker CLI is available, but the Docker engine is not reachable. Please start Docker Desktop / Docker Engine."
fi

require_cmd openclaw

if [ ! -d "$FIXTURES_WS" ]; then
  die "Missing fixtures workspace directory: $FIXTURES_WS"
fi

log "Preparing workspace directory: $WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR"

log "Creating fixtures default directory structure (no placeholder files)"

PROJECT_ID_DIR="$WORKSPACE_DIR/projects/wawa.proj.default"
AGENTS_DIR="$WORKSPACE_DIR/agents"

mkdir -p "$PROJECT_ID_DIR/todos" \
  "$PROJECT_ID_DIR/waiting_for_verification" \
  "$PROJECT_ID_DIR/finished"

mkdir -p "$AGENTS_DIR/designers/default" \
  "$AGENTS_DIR/developers/default" \
  "$AGENTS_DIR/verifiers/default"

copy_md_no_clobber() {
  src_dir="$1"
  dst_dir="$2"

# Copy only *.md as ticket files; skip any possible placeholder files
  if [ -d "$src_dir" ]; then
    for f in "$src_dir"/*.md; do
      [ -e "$f" ] || continue
      base="$(basename -- "$f")"
      case "$base" in
        *placeholder*.md)
          continue
          ;;
      esac
      cp -n "$f" "$dst_dir"/
    done
  fi
}

# projects/wawa.proj.default
copy_md_no_clobber "$FIXTURES_WS/projects/wawa.proj.default/todos" "$PROJECT_ID_DIR/todos"
copy_md_no_clobber "$FIXTURES_WS/projects/wawa.proj.default/waiting_for_verification" "$PROJECT_ID_DIR/waiting_for_verification"
copy_md_no_clobber "$FIXTURES_WS/projects/wawa.proj.default/finished" "$PROJECT_ID_DIR/finished"

# agents/*/default（来自 fixtures）
copy_md_no_clobber "$FIXTURES_WS/agents/designers/default" "$AGENTS_DIR/designers/default"
copy_md_no_clobber "$FIXTURES_WS/agents/developers/default" "$AGENTS_DIR/developers/default"
copy_md_no_clobber "$FIXTURES_WS/agents/verifiers/default" "$AGENTS_DIR/verifiers/default"

log "Pull image (if needed) and start container"
docker pull "$IMAGE" >/dev/null 2>&1 || true

if docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  log "Found existing container: $CONTAINER_NAME. Removing and recreating it."
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${PORT}:${PORT}" \
  -e "WAWA_WORKSPACE_PATH=/workspace" \
  -v "${WORKSPACE_DIR}:/workspace" \
  "$IMAGE" >/dev/null

log "Done. Open http://localhost:${PORT}"
log "Container: $CONTAINER_NAME"
log "Mounted workspace: ${WORKSPACE_DIR} -> /workspace"

