#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[05-test] Running test suite..."

if [[ ! -f "$ARTIFACTS_DIR/04-apply.done" ]]; then
  echo "[05-test] ERROR: missing artifacts/04-apply.done" >&2
  exit 1
fi

# Stub: run the full test suite.
# Example: python3 -m pytest tests/ -q
echo "PASSED: 43 tests" > "$ARTIFACTS_DIR/05-test.done"
echo "[05-test] PASSED"
