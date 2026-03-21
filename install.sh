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

WORKSPACE_DIR="${HOME}/.wawa-kanban/workspace"
BIN_DIR="${HOME}/.wawa-kanban/bin"
LOCAL_BIN_DIR="${HOME}/.local/bin"

WAWA_WKANBAN_URL_DEFAULT="https://raw.githubusercontent.com/hex-hex/wawa-kanban/main/cli/wkanban"
WAWA_WKANBAN_URL="${WAWA_WKANBAN_URL:-$WAWA_WKANBAN_URL_DEFAULT}"

have_required_tool_or_die() {
  tool="$1"
  if ! have_cmd "$tool"; then
    die "Command not found: $tool. Please install it and ensure it is in your PATH."
  fi
}

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
    # -f: fail on HTTP errors, -s: silent, -S: show errors
    curl -fsSL "$url" -o "$out_path"
  else
    # -q: quiet, -O- would write to stdout, but we need a file path
    wget -q "$url" -O "$out_path"
  fi
}

WORKSPACE_PROJECTS_DIR="${WORKSPACE_DIR}/projects"
WORKSPACE_AGENTS_DIR="${WORKSPACE_DIR}/agents"
DEFAULT_PROJECT_DIR="${WORKSPACE_PROJECTS_DIR}/wawa.proj.default"

AGENTS_DEFAULT_DESIGNERS_DIR="${WORKSPACE_AGENTS_DIR}/designers/default"
AGENTS_DEFAULT_DEVELOPERS_DIR="${WORKSPACE_AGENTS_DIR}/developers/default"
AGENTS_DEFAULT_VERIFIER_CODE_DIR="${WORKSPACE_AGENTS_DIR}/verifiers/code-verifier"
AGENTS_DEFAULT_VERIFIER_GENERAL_DIR="${WORKSPACE_AGENTS_DIR}/verifiers/general-verifier"

require_curl_or_wget

have_required_tool_or_die docker
if ! docker info >/dev/null 2>&1; then
  die "Docker CLI is available, but the Docker engine is not reachable. Please start Docker Desktop / Docker Engine."
fi

have_required_tool_or_die openclaw

log "Preparing workspace directory: $WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR"

log "Creating base directory tree (directories only)"
mkdir -p \
  "$DEFAULT_PROJECT_DIR/todos" \
  "$DEFAULT_PROJECT_DIR/waiting_for_verification" \
  "$DEFAULT_PROJECT_DIR/finished" \
  "$AGENTS_DEFAULT_DESIGNERS_DIR" \
  "$AGENTS_DEFAULT_DEVELOPERS_DIR" \
  "$AGENTS_DEFAULT_VERIFIER_CODE_DIR" \
  "$AGENTS_DEFAULT_VERIFIER_GENERAL_DIR"

log "Installing wkanban from GitHub raw: $WAWA_WKANBAN_URL"
mkdir -p "$BIN_DIR"

TMP_WKANBAN="${TMPDIR:-/tmp}/wkanban.$$"
trap 'rm -f "$TMP_WKANBAN" >/dev/null 2>&1 || true' EXIT HUP INT TERM

download_to "$WAWA_WKANBAN_URL" "$TMP_WKANBAN"
sh -n "$TMP_WKANBAN" >/dev/null 2>&1 || die "Downloaded wkanban failed a syntax check."

install_path="${BIN_DIR}/wkanban"
mv -f "$TMP_WKANBAN" "$install_path"
chmod +x "$install_path"

log "Linking wkanban into ~/.local/bin"
mkdir -p "$LOCAL_BIN_DIR"
ln -sf "$install_path" "$LOCAL_BIN_DIR/wkanban"

log "Running: wkanban init"
"$install_path" init

