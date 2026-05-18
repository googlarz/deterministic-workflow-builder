#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[04-merge] Applying merge..."

if [[ ! -f "$ARTIFACTS_DIR/03-review.done" ]]; then
  echo "[04-merge] ERROR: approval not recorded" >&2
  exit 1
fi

# Stub: apply the patch to the working tree.
# Example: git apply "$ARTIFACTS_DIR/diff.patch" && git commit -m "Apply reviewed patch"
touch "$ARTIFACTS_DIR/04-merge.done"
echo "[04-merge] Done."
