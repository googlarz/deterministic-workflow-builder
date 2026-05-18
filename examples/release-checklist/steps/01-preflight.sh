#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

mkdir -p "$ARTIFACTS_DIR"

echo "[01-preflight] Running preflight checks..."

# Stub: verify the branch, test suite, and required files.
# Example:
#   git diff --quiet || { echo "Uncommitted changes"; exit 1; }
#   python3 -m pytest tests/ -q || { echo "Tests failing"; exit 1; }

touch "$ARTIFACTS_DIR/01-preflight.done"
echo "[01-preflight] Done."
