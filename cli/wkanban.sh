#!/usr/bin/env sh
set -eu

log() {
  echo "[wkanban] $*"
}

die() {
  echo "[wkanban][ERROR] $*" >&2
  exit 1
}

have_container() {
  docker inspect "$1" >/dev/null 2>&1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

WORKSPACE_DIR="${HOME}/.wawa-kanban/workspace"
BIN_DIR="${HOME}/.wawa-kanban/bin"
LOCAL_BIN_DIR="${HOME}/.local/bin"
WAWA_WKANBAN_URL_DEFAULT="https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/cli/wkanban.sh"
WAWA_WKANBAN_URL="${WAWA_WKANBAN_URL:-$WAWA_WKANBAN_URL_DEFAULT}"

CONTAINER_NAME="wawa-kanban"
IMAGE="wawaassistant/wawa-kanban:latest"
PORT="5020"
CONTAINER_APP_HOME="/home/appuser"

WAWA_OPENCLAW_LEAD_AGENT_ID="${WAWA_OPENCLAW_LEAD_AGENT_ID:-wawa-lead}"
WAWA_OPENCLAW_LEAD_INTRO_MESSAGE="${WAWA_OPENCLAW_LEAD_INTRO_MESSAGE:-introduce yourself.}"

require_curl_or_wget() {
  if have_cmd curl; then
    DOWNLOADER="curl"
    return 0
  fi
  if have_cmd wget; then
    DOWNLOADER="wget"
    return 0
  fi
  die "Neither 'curl' nor 'wget' is available. Please install one of them and ensure it is in your PATH."
}

download_to() {
  url="$1"
  out_path="$2"
  if [ "$DOWNLOADER" = "curl" ]; then
    curl -fsSL "$url" -o "$out_path"
  else
    wget -q "$url" -O "$out_path"
  fi
}

update_wkanban_script() {
  require_curl_or_wget
  mkdir -p "$BIN_DIR"
  mkdir -p "$LOCAL_BIN_DIR"

  tmp_script="${TMPDIR:-/tmp}/wkanban.update.$$"
  trap 'rm -f "$tmp_script" >/dev/null 2>&1 || true' EXIT HUP INT TERM

  log "Downloading latest wkanban script: $WAWA_WKANBAN_URL"
  download_to "$WAWA_WKANBAN_URL" "$tmp_script"
  sh -n "$tmp_script" >/dev/null 2>&1 || die "Downloaded wkanban failed a syntax check."

  install_path="${BIN_DIR}/wkanban"
  mv -f "$tmp_script" "$install_path"
  chmod +x "$install_path"
  ln -sf "$install_path" "${LOCAL_BIN_DIR}/wkanban"
  log "Updated local wkanban script: $install_path"
}

ephemeral_kanban_run() {
  docker pull "$IMAGE" >/dev/null 2>&1 || true
  docker run --rm \
    -w /app \
    -e WAWA_WORKSPACE_PATH=/workspace \
    -e HOME="${CONTAINER_APP_HOME}" \
    -e "PUID=$(id -u)" \
    -e "PGID=$(id -g)" \
    -v "${WORKSPACE_DIR}:/workspace" \
    -v "${HOME}/.openclaw:${CONTAINER_APP_HOME}/.openclaw" \
    "$IMAGE" \
    "$@"
}

docker_start() {
  mkdir -p "${HOME}/.openclaw"

  log "Pulling image (if needed): $IMAGE"
  docker pull "$IMAGE" >/dev/null 2>&1 || true

  if have_container "$CONTAINER_NAME"; then
    log "Found existing container: $CONTAINER_NAME. Removing and recreating it."
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi

  log "Starting container..."
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "0.0.0.0:${PORT}:${PORT}" \
    -e "WAWA_WORKSPACE_PATH=/workspace" \
    -e "HOME=${CONTAINER_APP_HOME}" \
    -e "PUID=$(id -u)" \
    -e "PGID=$(id -g)" \
    -v "${WORKSPACE_DIR}:/workspace" \
    -v "${HOME}/.openclaw:${CONTAINER_APP_HOME}/.openclaw" \
    "$IMAGE" >/dev/null

  log "Done. Open http://localhost:${PORT}"
}

docker_stop_remove() {
  if have_container "$CONTAINER_NAME"; then
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

openclaw_lead_intro() {
  if [ "${WAWA_SKIP_OPENCLAW_LEAD_INTRO:-0}" = "1" ]; then
    log "Skipping OpenClaw lead intro (WAWA_SKIP_OPENCLAW_LEAD_INTRO=1)."
    return 0
  fi
  if ! command -v openclaw >/dev/null 2>&1; then
    log "OpenClaw CLI not in PATH; skipping lead intro. With gateway running: openclaw agent --agent ${WAWA_OPENCLAW_LEAD_AGENT_ID} --message \"${WAWA_OPENCLAW_LEAD_INTRO_MESSAGE}\""
    return 0
  fi
  log "OpenClaw: one agent turn for ${WAWA_OPENCLAW_LEAD_AGENT_ID} (session bootstrap)..."
  if ! openclaw agent --agent "${WAWA_OPENCLAW_LEAD_AGENT_ID}" --message "${WAWA_OPENCLAW_LEAD_INTRO_MESSAGE}"; then
    log "OpenClaw lead intro failed (is the gateway running?). Continuing."
  fi
}

init() {
  mkdir -p "$WORKSPACE_DIR"
  mkdir -p "${HOME}/.openclaw"
  docker_start
  log "Seeding default project and agents (inside container, same as wkanban CLI)..."
  docker exec -w /app "$CONTAINER_NAME" uv run wkanban project add default -y --workspace /workspace
  docker exec -w /app "$CONTAINER_NAME" uv run wkanban agent add-default --workspace /workspace
  openclaw_lead_intro
  log "Init complete."
}

update() {
  log "Updating wkanban script, image, and restarting with existing parameters..."
  update_wkanban_script
  mkdir -p "$WORKSPACE_DIR"
  mkdir -p "${HOME}/.openclaw"
  docker_start
  log "Syncing guidance files from latest templates..."
  docker exec -w /app "$CONTAINER_NAME" uv run wkanban agent sync --state-dir "${CONTAINER_APP_HOME}/.openclaw"
  log "Update complete."
}

uninstall() {
  force="0"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --force|-f)
        force="1"
        shift
        ;;
      *)
        die "Unknown uninstall option: $1"
        ;;
    esac
  done

  log "Uninstalling..."
  docker_stop_remove

  host_openclaw_cfg="${HOME}/.openclaw/openclaw.json"
  if [ -f "$host_openclaw_cfg" ]; then
    ts="$(date +"%Y%m%d-%H%M%S")"
    host_openclaw_backup="${host_openclaw_cfg}.bak.uninstall.${ts}"
    cp "$host_openclaw_cfg" "$host_openclaw_backup"
    log "Backed up openclaw.json to: ${host_openclaw_backup}"
  else
    log "No host openclaw.json found at ${host_openclaw_cfg}; skipping pre-uninstall backup."
  fi

  if [ -d "${HOME}/.openclaw" ]; then
    log "Analyzing potential uninstall residuals (inside one-shot container)..."
    analyze_rc="0"
    if ephemeral_kanban_run uv run wkanban agent analyze-uninstall --state-dir "${CONTAINER_APP_HOME}/.openclaw"; then
      analyze_rc="0"
    else
      analyze_rc="$?"
    fi
    if [ "$analyze_rc" -eq 3 ] && [ "$force" != "1" ]; then
      die "Possible residual detected. Aborting uninstall. Re-run with: wkanban uninstall --force"
    elif [ "$analyze_rc" -ne 0 ]; then
      die "Uninstall analyze failed with exit code: $analyze_rc"
    fi

    log "Cleaning up agents from openclaw.json (inside one-shot container)..."
    ephemeral_kanban_run uv run wkanban agent uninstall-all --state-dir "${CONTAINER_APP_HOME}/.openclaw"
  else
    log "Skipping OpenClaw cleanup (~/.openclaw missing)."
  fi

  rm -f "${LOCAL_BIN_DIR}/wkanban" >/dev/null 2>&1 || true
  rm -f "${BIN_DIR}/wkanban" >/dev/null 2>&1 || true
  rm -rf "$WORKSPACE_DIR" >/dev/null 2>&1 || true
  log "Uninstalled. Workspace removed."
}

require_uv_and_repo() {
  _ctx="$1"
  if ! command -v uv >/dev/null 2>&1; then
    die "Command not found: uv. Install from https://docs.astral.sh/uv/ — required for ${_ctx}."
  fi
  root="${WAWA_KANBAN_ROOT:-}"
  if [ -z "$root" ]; then
    die "Set WAWA_KANBAN_ROOT to your wawa-kanban git clone, then run: wkanban ${_ctx} ..."
  fi
  if [ ! -d "$root" ]; then
    die "WAWA_KANBAN_ROOT is not a directory: $root"
  fi
}

wkanban_py_via_uv() {
  require_uv_and_repo "agent|project|…"
  (cd "$root" && uv run wkanban "$@")
}

cmd="${1:-}"
case "$cmd" in
  init)
    init
    ;;
  update)
    update
    ;;
  uninstall)
    shift
    uninstall "$@"
    ;;
  agent|project)
    wkanban_py_via_uv "$@"
    ;;
  *)
    die "Usage: wkanban {init|update|uninstall|agent|project} ..."
    ;;
esac

