#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STEP_ID="02-verify"

GREETING="$ROOT_DIR/artifacts/01-greet.txt"

if [[ ! -f "$GREETING" ]]; then
    echo "[$STEP_ID] ERROR: expected artifact $GREETING not found" >&2
    exit 1
fi

if ! grep -q "Hello from deterministic-workflow-builder" "$GREETING"; then
    echo "[$STEP_ID] ERROR: greeting artifact did not contain expected text" >&2
    exit 1
fi

mkdir -p "$ROOT_DIR/artifacts"
echo "verified: $(cat "$GREETING")" > "$ROOT_DIR/artifacts/02-verify.done"
echo "[$STEP_ID] greeting verified successfully"
