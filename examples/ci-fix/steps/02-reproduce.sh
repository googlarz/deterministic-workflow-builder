#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[02-reproduce] Reproducing failure locally..."

if [[ ! -f "$ARTIFACTS_DIR/failing-test-output.txt" ]]; then
  echo "[02-reproduce] ERROR: missing artifacts/failing-test-output.txt" >&2
  exit 1
fi

# Stub: run the exact failing test to confirm reproduction.
# Example: python3 -m pytest tests/test_example.py::test_something --no-header -q

touch "$ARTIFACTS_DIR/02-reproduce.done"
echo "[02-reproduce] Done."
