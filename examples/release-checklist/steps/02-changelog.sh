#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[02-changelog] Verifying CHANGELOG..."

# Stub: verify CHANGELOG.md has an entry for the release version.
# Example:
#   VERSION=$(cat VERSION)
#   grep -q "## $VERSION" CHANGELOG.md || { echo "Missing changelog entry for $VERSION"; exit 1; }

touch "$ARTIFACTS_DIR/02-changelog.done"
echo "[02-changelog] Done."
