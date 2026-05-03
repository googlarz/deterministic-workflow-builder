#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rm -f "$ROOT_DIR/artifacts/02-verify.done"
echo "[02-verify rollback] removed artifacts/02-verify.done"
