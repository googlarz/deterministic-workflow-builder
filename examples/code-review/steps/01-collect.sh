#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$WORKFLOW_DIR/artifacts"

mkdir -p "$ARTIFACTS_DIR"

echo "[01-collect] Gathering diff..."

# Stub: capture the diff from the current branch vs main.
# Example: git diff origin/main...HEAD > "$ARTIFACTS_DIR/diff.patch"
cat > "$ARTIFACTS_DIR/diff.patch" <<'EOF'
--- a/src/example.py
+++ b/src/example.py
@@ -1,3 +1,4 @@
 def hello():
-    return "hello"
+    # improved greeting
+    return "hello, world"
EOF

echo "[01-collect] Done. Artifact: artifacts/diff.patch"
