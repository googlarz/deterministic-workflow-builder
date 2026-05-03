# hello-world

## Deterministic Workflow Contract

Goal: Greet the user and verify the greeting was written.

Inputs: none

Outputs:
- `artifacts/02-verify.done` — proof that greeting was verified

Runtime:
- `./run_workflow.sh`
- `./workflow.json`

Policy Pack:
- `strict-prod`

Steps:
1. `greet` — write a greeting to `artifacts/01-greet.txt`
2. `verify` — confirm the greeting artifact exists and contains the expected text

Failure policy:
- Stop on first failed step.

Residual nondeterminism: none
