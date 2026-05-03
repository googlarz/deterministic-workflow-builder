#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rm -f "$ROOT_DIR/artifacts/01-greet.txt"
echo "[01-greet rollback] removed artifacts/01-greet.txt"
