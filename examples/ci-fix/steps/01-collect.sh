#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

mkdir -p "$ARTIFACTS_DIR"

echo "[01-collect] Collecting failing test output..."

# Stub: in a real workflow, run the failing test suite and capture output.
# Example: python3 -m pytest tests/ -x 2>&1 | tee "$ARTIFACTS_DIR/failing-test-output.txt"
# For this template, write a placeholder artifact.
cat > "$ARTIFACTS_DIR/failing-test-output.txt" <<'EOF'
FAILED tests/test_example.py::test_something - AssertionError: expected True, got False
1 failed, 42 passed
EOF

echo "[01-collect] Done. Artifact: artifacts/failing-test-output.txt"
