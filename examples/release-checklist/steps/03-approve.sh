#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[03-approve] Release approval gate — waiting for explicit --approve 03-approve"
echo "  Run: python3 scripts/run_workflow.py examples/release-checklist --approve 03-approve --approval-reason 'Release verified'"

# This step requires_approval: true. The runner blocks until operator approves.
touch "$ARTIFACTS_DIR/03-approve.done"
echo "[03-approve] Approval recorded."
