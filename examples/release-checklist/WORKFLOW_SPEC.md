# Release Checklist Workflow

## Goal

Ship a release safely with deterministic gates: preflight validation, changelog verification, human approval, git tag, and post-release smoke test.

## Steps

| Step | Type | Description |
|------|------|-------------|
| 01-preflight | shell | Verify clean branch, passing tests, required files |
| 02-changelog | shell | Confirm CHANGELOG has an entry for the release version |
| 03-approve | approval | Human gate — blocks until `--approve 03-approve` |
| 04-tag | shell | Create and push the git release tag |
| 05-verify | test | Post-release smoke test |

## Approval Gate

```bash
python3 scripts/run_workflow.py examples/release-checklist --approve 03-approve --approval-reason "Release v1.2.0 verified"
```

## Usage

```bash
python3 scripts/verify_workflow.py examples/release-checklist --simulate
python3 scripts/run_workflow.py examples/release-checklist --list
python3 scripts/run_workflow.py examples/release-checklist --dry-run
python3 scripts/run_workflow.py examples/release-checklist
```
