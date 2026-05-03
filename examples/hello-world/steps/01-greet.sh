#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STEP_ID="01-greet"

mkdir -p "$ROOT_DIR/artifacts"

echo "Hello from deterministic-workflow-builder!" > "$ROOT_DIR/artifacts/01-greet.txt"
echo "Run at: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ROOT_DIR/artifacts/01-greet.txt"

echo "[$STEP_ID] wrote artifacts/01-greet.txt"
