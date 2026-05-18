# CI Fix Workflow

## Goal

Fix a failing CI test deterministically by reproducing the failure locally, generating ranked fix candidates, applying the best candidate, and verifying the full test suite passes.

## Inputs

- `artifacts/failing-test-output.txt` — captured output from the failing CI run (produced by step 01-collect if not pre-supplied)

## Outputs

- `artifacts/05-test.done` — proof that the test suite passed after the fix was applied

## Steps

| Step | Type | Description |
|------|------|-------------|
| 01-collect | shell | Capture the failing test output |
| 02-reproduce | shell | Reproduce the failure in the local environment |
| 03-candidate-fixes | shell | Generate deterministic fix candidates ranked by confidence |
| 04-apply | shell | Apply the highest-ranked candidate |
| 05-test | test | Run the full test suite and verify all tests pass |

## Approval Gates

None — fully automated. Add `"requires_approval": true` on 04-apply if human sign-off is needed before patching source files.

## Residual Nondeterminism

- Network state during test execution may vary

## Usage

```bash
# Verify the workflow
python3 scripts/verify_workflow.py examples/ci-fix --simulate

# Run with dry-run first
python3 scripts/run_workflow.py examples/ci-fix --dry-run --list

# Run
python3 scripts/run_workflow.py examples/ci-fix
```
