#!/usr/bin/env python3
"""Notify a webhook when workflow steps are pending approval."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_tsv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line.strip():
            continue
        key, value = line.split("\t", 1)
        result[key] = value
    return result


def load_manifest(workflow_dir: Path) -> dict:
    manifest_path = workflow_dir / "workflow.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing workflow.json in {workflow_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def find_pending_approvals(workflow_dir: Path, manifest: dict) -> list[dict]:
    step_state_path = workflow_dir / "state" / "step-status.tsv"
    step_state = read_tsv(step_state_path)

    pending: list[dict] = []
    for step in manifest.get("steps", []):
        step_id = step.get("id", "")
        status = step_state.get(step_id, "pending")
        if status == "pending-approval" or (
            step.get("requires_approval") and status == "pending"
        ):
            pending.append({
                "step_id": step_id,
                "step_name": step.get("name", step_id),
                "requires_approval": bool(step.get("requires_approval")),
                "approve_command": (
                    f"python3 scripts/run_workflow.py {workflow_dir} --approve {step_id}"
                ),
            })
    return pending


def build_generic_payload(workflow_dir: Path, manifest: dict, pending: list[dict]) -> dict:
    return {
        "workflow_name": manifest.get("workflow_name", str(workflow_dir.name)),
        "workflow_dir": str(workflow_dir),
        "pending_approvals": pending,
        "timestamp": utc_now(),
    }


def build_slack_payload(workflow_dir: Path, manifest: dict, pending: list[dict]) -> dict:
    wf_name = manifest.get("workflow_name", str(workflow_dir.name))
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Approval required: {wf_name}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Workflow:* `{wf_name}`\n*Directory:* `{workflow_dir}`",
            },
        },
    ]
    for item in pending:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Step:* `{item['step_id']}` — {item['step_name']}\n"
                    f"*Approve with:*\n```{item['approve_command']}```"
                ),
            },
        })
    blocks.append({"type": "divider"})
    return {"blocks": blocks, "text": f"Approval required for {wf_name}"}


def post_json(url: str, payload: dict) -> int:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Notify a webhook when workflow steps are pending approval."
    )
    parser.add_argument("workflow_dir", help="Workflow directory path.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--webhook-url", help="POST payload to this URL.")
    group.add_argument("--slack", metavar="WEBHOOK_URL", help="POST Slack Block Kit message to this URL.")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending.")
    parser.add_argument(
        "--poll",
        type=int,
        metavar="SECONDS",
        help="Poll every N seconds until no pending approvals remain.",
    )
    return parser.parse_args(argv)


def run_once(args: argparse.Namespace) -> int:
    workflow_dir = Path(args.workflow_dir).resolve()
    manifest = load_manifest(workflow_dir)
    pending = find_pending_approvals(workflow_dir, manifest)

    if not pending:
        print("[approval-notifier] No pending approvals.")
        return 0

    if args.slack:
        payload = build_slack_payload(workflow_dir, manifest, pending)
        url = args.slack
    else:
        payload = build_generic_payload(workflow_dir, manifest, pending)
        url = args.webhook_url

    if args.dry_run:
        print("[approval-notifier] Dry run — would POST:")
        print(json.dumps(payload, indent=2))
        return 0

    if not url:
        print("[approval-notifier] ERROR: --webhook-url or --slack required when not using --dry-run", file=sys.stderr)
        return 1

    try:
        status = post_json(url, payload)
        print(f"[approval-notifier] Posted. HTTP {status}. Pending steps: {[p['step_id'] for p in pending]}")
    except Exception as exc:
        print(f"[approval-notifier] ERROR: {exc}", file=sys.stderr)
        return 1

    return len(pending)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.poll is not None:
        interval = max(1, args.poll)
        while True:
            remaining = run_once(args)
            if remaining == 0:
                print("[approval-notifier] All approvals resolved. Exiting.")
                return 0
            print(f"[approval-notifier] Polling again in {interval}s...")
            time.sleep(interval)
    else:
        result = run_once(args)
        return 0 if result == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
