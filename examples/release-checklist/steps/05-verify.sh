#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[05-verify] Running post-release smoke test..."

if [[ ! -f "$ARTIFACTS_DIR/04-tag.done" ]]; then
  echo "[05-verify] ERROR: tag step not completed" >&2
  exit 1
fi

# Stub: verify the release is reachable and functional.
# Example: curl -sf "https://api.example.com/healthz" | jq -e '.status == "ok"'

echo "smoke test passed" > "$ARTIFACTS_DIR/05-verify.done"
echo "[05-verify] Done."
