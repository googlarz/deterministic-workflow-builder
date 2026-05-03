#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Installed skill (standard Codex/Claude Code location)
CODEX_SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/deterministic-workflow-builder"

# 2. Repo root fallback — works when running from a git clone
REPO_SKILL_HOME="$(cd "$ROOT_DIR/../.." && pwd)"

if [[ -f "$CODEX_SKILL_HOME/scripts/run_workflow.py" ]]; then
  exec python3 "$CODEX_SKILL_HOME/scripts/run_workflow.py" --workflow-dir "$ROOT_DIR" "$@"
elif [[ -f "$REPO_SKILL_HOME/scripts/run_workflow.py" ]]; then
  exec python3 "$REPO_SKILL_HOME/scripts/run_workflow.py" --workflow-dir "$ROOT_DIR" "$@"
else
  echo "ERROR: Cannot find run_workflow.py." >&2
  echo "  Install the skill: cp -r . ~/.codex/skills/deterministic-workflow-builder" >&2
  echo "  Or run directly:   python3 scripts/run_workflow.py examples/hello-world" >&2
  exit 2
fi
