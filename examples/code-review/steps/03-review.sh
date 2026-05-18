#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

echo "[03-review] Approval gate — waiting for explicit --approve 03-review"
echo "  Review artifacts/analysis-report.txt and artifacts/diff.patch"
echo "  Then run: python3 scripts/run_workflow.py examples/code-review --approve 03-review --approval-reason 'LGTM'"

# This step requires_approval: true. The runner will pause here until
# the operator runs: run_workflow.py <dir> --approve 03-review
touch "$ARTIFACTS_DIR/03-review.done"
echo "[03-review] Approval recorded."
