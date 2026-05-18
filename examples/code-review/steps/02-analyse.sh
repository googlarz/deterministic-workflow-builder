#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[02-analyse] Running static analysis..."

if [[ ! -f "$ARTIFACTS_DIR/diff.patch" ]]; then
  echo "[02-analyse] ERROR: missing artifacts/diff.patch" >&2
  exit 1
fi

# Stub: run linting and static analysis on the changed files.
# Example: flake8 $(git diff --name-only origin/main...HEAD | grep '\.py$')
cat > "$ARTIFACTS_DIR/analysis-report.txt" <<'EOF'
Static analysis report
======================
Files changed: src/example.py
Lint: OK (0 issues)
Type check: OK
Complexity: 1 function, cyclomatic=1
EOF

echo "[02-analyse] Done. Artifact: artifacts/analysis-report.txt"
