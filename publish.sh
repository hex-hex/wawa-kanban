#!/usr/bin/env sh
set -eu

# Publish Docker image to a registry.
# - Builds :latest
# - Tags and pushes the current git short hash

IMAGE_REPO="${1:-wawaassistant/wawa-kanban}"

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

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

