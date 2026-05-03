# hello-world

The simplest complete example: two steps, no AI, no approvals, no external dependencies.

**Step 1 — greet:** writes a greeting to `artifacts/01-greet.txt`.
**Step 2 — verify:** reads that artifact and checks it contains the expected text.

## Run it

From the repo root:

```bash
# Preview — no execution
python3 scripts/run_workflow.py examples/hello-world --list
python3 scripts/run_workflow.py examples/hello-world --dry-run

# Execute
python3 scripts/run_workflow.py examples/hello-world

# Inspect output
cat examples/hello-world/artifacts/01-greet.txt
cat examples/hello-world/artifacts/02-verify.done

# Reset and run again
python3 scripts/run_workflow.py examples/hello-world --reset
python3 scripts/run_workflow.py examples/hello-world
```

## What you see

```
  → running  01-greet
  ✓ complete 01-greet  (0.0s)
  → running  02-verify
  ✓ complete 02-verify  (0.0s)
```

## What this demonstrates

- `workflow.json` schema v4 with two sequential steps
- `depends_on` to express the DAG edge between steps
- `produces` / `consumes` artifact contracts
- `success_gate` tied to a deterministic file-existence check
- `rollback` scripts registered per step
- `offline` network mode — nothing phones home
- `strict-prod` policy pack
