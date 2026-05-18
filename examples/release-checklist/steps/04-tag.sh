#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[04-tag] Creating git tag..."

if [[ ! -f "$ARTIFACTS_DIR/03-approve.done" ]]; then
  echo "[04-tag] ERROR: release not approved" >&2
  exit 1
fi

# Stub: create the release tag.
# Example:
#   VERSION=$(cat VERSION)
#   git tag -a "v$VERSION" -m "Release v$VERSION"
#   git push origin "v$VERSION"

touch "$ARTIFACTS_DIR/04-tag.done"
echo "[04-tag] Done."
