# Code Review Workflow

## Goal

Perform a deterministic code review: gather the diff, run static analysis, require explicit human approval, then apply the merge.

## Inputs

- `artifacts/diff.patch` — the patch to review (produced by step 01-collect if not pre-supplied)

## Outputs

- `artifacts/04-merge.done` — proof that the approved patch was merged

## Steps

| Step | Type | Description |
|------|------|-------------|
| 01-collect | shell | Capture the diff from the current branch |
| 02-analyse | shell | Run static analysis and lint on changed files |
| 03-review | approval | Human approval gate — blocks until `--approve 03-review` |
| 04-merge | shell | Apply the approved patch |

## Approval Gate

Step 03-review requires explicit approval:

```bash
python3 scripts/run_workflow.py examples/code-review --approve 03-review --approval-reason "LGTM, analysis clean"
```

## Usage

```bash
python3 scripts/verify_workflow.py examples/code-review --simulate
python3 scripts/run_workflow.py examples/code-review --list
python3 scripts/run_workflow.py examples/code-review
```
