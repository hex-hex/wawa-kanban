#!/usr/bin/env sh
set -eu

# Publish Docker image to a registry.
# - Builds :latest
# - Tags and pushes the current git short hash

IMAGE_REPO="${1:-wawaassistant/wawa-kanban}"

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

# Require default branch, up-to-date with origin, no merge conflicts before publishing.
DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|^refs/remotes/origin/||')"
if [ -z "$DEFAULT_BRANCH" ]; then
  for b in main master; do
    if git show-ref --verify --quiet "refs/remotes/origin/$b" 2>/dev/null; then
      DEFAULT_BRANCH="$b"
      break
    fi
  done
fi
if [ -z "$DEFAULT_BRANCH" ]; then
  echo "[publish] ERROR: could not determine default branch (origin/HEAD or origin/main|master)." >&2
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
if [ -z "$CURRENT_BRANCH" ]; then
  echo "[publish] ERROR: detached HEAD; checkout '${DEFAULT_BRANCH}' first." >&2
  exit 1
fi
if [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  echo "[publish] ERROR: must be on default branch '${DEFAULT_BRANCH}' (currently '${CURRENT_BRANCH}')." >&2
  exit 1
fi

echo "[publish] syncing: fetch + pull --ff-only origin/${DEFAULT_BRANCH}"
git fetch origin
if ! git pull --ff-only "origin" "$DEFAULT_BRANCH"; then
  echo "[publish] ERROR: pull did not fast-forward (diverged history or other failure). Fix and retry." >&2
  exit 1
fi
if [ -n "$(git diff --name-only --diff-filter=U 2>/dev/null || true)" ]; then
  echo "[publish] ERROR: unresolved merge conflicts in working tree." >&2
  exit 1
fi

COMMIT_SHORT="$(git rev-parse --short HEAD)"

echo "[publish] building: ${IMAGE_REPO}:latest"
docker build -t "${IMAGE_REPO}:latest" .

echo "[publish] pushing: ${IMAGE_REPO}:latest"
docker push "${IMAGE_REPO}:latest"

echo "[publish] tagging: ${IMAGE_REPO}:latest -> ${IMAGE_REPO}:${COMMIT_SHORT}"
docker tag "${IMAGE_REPO}:latest" "${IMAGE_REPO}:${COMMIT_SHORT}"

echo "[publish] pushing: ${IMAGE_REPO}:${COMMIT_SHORT}"
docker push "${IMAGE_REPO}:${COMMIT_SHORT}"

echo "[publish] done: ${IMAGE_REPO}:latest and ${IMAGE_REPO}:${COMMIT_SHORT}"

