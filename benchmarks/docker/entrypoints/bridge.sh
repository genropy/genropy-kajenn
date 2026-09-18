#!/bin/bash
# The bridge stack: genropy + kajenn + genropy-kajenn from the mounted
# trees, then the SPA pool. Knobs arrive from the compose environment
# (KAJENN_WORKER_MAX_USERS, KAJENN_INSPECTOR, GNR_DAEMON_PROVIDER).
set -e
# setuptools writes egg-info into the source tree, and the mount is
# read-only: install from a throwaway copy instead.
uv pip install --system --quiet /src/kajenn /src/genropy-kajenn
if [ -n "${KAJENN_POOL_RECIPE:-}" ]; then
  exec gnrkajenn bridge_lab -H 0.0.0.0 -p 8098 --nodebug --config "$KAJENN_POOL_RECIPE"
fi
exec gnrkajenn bridge_lab -H 0.0.0.0 -p 8098 --nodebug
