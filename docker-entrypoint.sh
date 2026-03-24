#!/bin/sh
set -eu

# Run the app as PUID:PGID so bind mounts (~/.openclaw, workspace) get the same numeric
# ownership as the host user. Defaults preserve the previous image behavior (1000:1000).
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

if [ "$(id -u)" -eq 0 ]; then
  chown -R "${PUID}:${PGID}" /app
  chown -R "${PUID}:${PGID}" /home/appuser
  if [ -d /workspace ]; then
    chown -R "${PUID}:${PGID}" /workspace
  fi
  exec setpriv --reuid="${PUID}" --regid="${PGID}" --clear-groups -- "$@"
fi

exec "$@"
