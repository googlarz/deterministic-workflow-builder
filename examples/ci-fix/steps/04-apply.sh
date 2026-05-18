#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[04-apply] Applying best fix candidate..."

if [[ ! -f "$ARTIFACTS_DIR/fix-candidates.txt" ]]; then
  echo "[04-apply] ERROR: missing artifacts/fix-candidates.txt" >&2
  exit 1
fi

# Stub: parse candidate-1 from fix-candidates.txt and apply it.
# In a real workflow this would use sed/patch to modify source files.
echo "Applied candidate-1 from fix-candidates.txt" > "$ARTIFACTS_DIR/04-apply.done"
echo "[04-apply] Done."
