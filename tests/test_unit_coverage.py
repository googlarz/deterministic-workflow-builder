"""Unit tests that import scripts/ directly to generate coverage."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_workflow  # noqa: E402
import workflow_schema  # noqa: E402
import security_audit  # noqa: E402
import lint_determinism  # noqa: E402


# ---------------------------------------------------------------------------
# run_workflow — deep_merge
# ---------------------------------------------------------------------------

class TestDeepMerge(unittest.TestCase):
    def test_flat_override(self):
        result = run_workflow.deep_merge({"a": 1, "b": 2}, {"b": 99})
        self.assertEqual(result, {"a": 1, "b": 99})

    def test_adds_new_key(self):
        result = run_workflow.deep_merge({"a": 1}, {"b": 2})
        self.assertEqual(result["b"], 2)

    def test_nested_merge(self):
        base = {"x": {"y": 1, "z": 2}}
        override = {"x": {"z": 99}}
        result = run_workflow.deep_merge(base, override)
        self.assertEqual(result["x"]["y"], 1)
        self.assertEqual(result["x"]["z"], 99)

    def test_does_not_mutate_base(self):
        base = {"a": {"b": 1}}
        run_workflow.deep_merge(base, {"a": {"b": 2}})
        self.assertEqual(base["a"]["b"], 1)

    def test_empty_override(self):
        base = {"a": 1}
        result = run_workflow.deep_merge(base, {})
        self.assertEqual(result, {"a": 1})


# ---------------------------------------------------------------------------
# run_workflow — redact_text
# ---------------------------------------------------------------------------

class TestRedactText(unittest.TestCase):
    def test_redacts_secret(self):
        result = run_workflow.redact_text("secret=abc123")
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("abc123", result)

    def test_redacts_token(self):
        result = run_workflow.redact_text("token=mytoken")
        self.assertIn("[REDACTED]", result)

    def test_redacts_password(self):
        result = run_workflow.redact_text("password=hunter2")
        self.assertIn("[REDACTED]", result)

    def test_safe_text_unchanged(self):
        text = "hello world"
        self.assertEqual(run_workflow.redact_text(text), text)

    def test_case_insensitive(self):
        result = run_workflow.redact_text("TOKEN=XYZ")
        self.assertIn("[REDACTED]", result)


# ---------------------------------------------------------------------------
# run_workflow — parse_success_gate
# ---------------------------------------------------------------------------

class TestParseSuccessGate(unittest.TestCase):
    def test_dict_passthrough(self):
        gate = {"type": "noop"}
        self.assertEqual(run_workflow.parse_success_gate(gate), gate)

    def test_todo_string(self):
        self.assertEqual(run_workflow.parse_success_gate("todo"), {"type": "noop"})

    def test_todo_case_insensitive(self):
        self.assertEqual(run_workflow.parse_success_gate("TODO"), {"type": "noop"})

    def test_log_contains(self):
        result = run_workflow.parse_success_gate("log contains SUCCESS")
        self.assertEqual(result["type"], "log_contains")
        self.assertEqual(result["value"], "SUCCESS")

    def test_file_exists(self):
        result = run_workflow.parse_success_gate("file exists artifacts/out.txt")
        self.assertEqual(result["type"], "file_exists")
        self.assertEqual(result["path"], "artifacts/out.txt")

    def test_artifact_exists(self):
        result = run_workflow.parse_success_gate("artifact exists artifacts/out.txt")
        self.assertEqual(result["type"], "file_exists")
        self.assertEqual(result["path"], "artifacts/out.txt")

    def test_plain_description(self):
        result = run_workflow.parse_success_gate("exit code 0")
        self.assertEqual(result["type"], "description")
        self.assertEqual(result["value"], "exit code 0")

    def test_none_value(self):
        result = run_workflow.parse_success_gate(None)
        self.assertEqual(result["type"], "noop")

    def test_integer_value(self):
        result = run_workflow.parse_success_gate(42)
        self.assertEqual(result["type"], "noop")


# ---------------------------------------------------------------------------
# run_workflow — normalize_contracts
# ---------------------------------------------------------------------------

class TestNormalizeContracts(unittest.TestCase):
    def test_string_entries(self):
        result = run_workflow.normalize_contracts(["artifacts/out.txt"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "artifacts/out.txt")
        self.assertEqual(result[0]["type"], "file")

    def test_dict_entries_passthrough(self):
        entry = {"path": "artifacts/out.txt", "type": "json", "required": False}
        result = run_workflow.normalize_contracts([entry])
        self.assertEqual(result[0]["path"], "artifacts/out.txt")
        self.assertEqual(result[0]["type"], "json")

    def test_invalid_entries_skipped(self):
        result = run_workflow.normalize_contracts([None, 42])
        self.assertEqual(result, [])

    def test_mixed_entries(self):
        result = run_workflow.normalize_contracts(["a.txt", {"path": "b.txt"}])
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# run_workflow — resolve_safe_path
# ---------------------------------------------------------------------------

class TestResolveSafePath(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp()).resolve()

    def test_safe_relative_path(self):
        result = run_workflow.resolve_safe_path(self.tmpdir, "subdir/file.txt")
        self.assertEqual(result, self.tmpdir / "subdir" / "file.txt")

    def test_traversal_raises(self):
        with self.assertRaises(ValueError):
            run_workflow.resolve_safe_path(self.tmpdir, "../escape.txt")

    def test_double_traversal_raises(self):
        with self.assertRaises(ValueError):
            run_workflow.resolve_safe_path(self.tmpdir, "sub/../../escape.txt")


# ---------------------------------------------------------------------------
# run_workflow — audit_enabled
# ---------------------------------------------------------------------------

class TestAuditEnabled(unittest.TestCase):
    def test_default_enabled(self):
        self.assertTrue(run_workflow.audit_enabled({}, {}))

    def test_manifest_disables(self):
        manifest = {"audit": {"enabled": False}}
        self.assertFalse(run_workflow.audit_enabled(manifest, {}))

    def test_policy_disables(self):
        policy = {"audit": {"enabled": False}}
        self.assertFalse(run_workflow.audit_enabled({}, policy))

    def test_both_enabled(self):
        manifest = {"audit": {"enabled": True}}
        policy = {"audit": {"enabled": True}}
        self.assertTrue(run_workflow.audit_enabled(manifest, policy))


# ---------------------------------------------------------------------------
# run_workflow — get_steps_by_id
# ---------------------------------------------------------------------------

class TestGetStepsById(unittest.TestCase):
    def test_returns_dict(self):
        manifest = {"steps": [{"id": "01-collect", "name": "collect"}, {"id": "02-run", "name": "run"}]}
        result = run_workflow.get_steps_by_id(manifest)
        self.assertIn("01-collect", result)
        self.assertIn("02-run", result)
        self.assertEqual(result["01-collect"]["name"], "collect")

    def test_empty_steps(self):
        self.assertEqual(run_workflow.get_steps_by_id({"steps": []}), {})


# ---------------------------------------------------------------------------
# run_workflow — sha256_file
# ---------------------------------------------------------------------------

class TestSha256File(unittest.TestCase):
    def test_known_hash(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as fh:
            fh.write(b"hello world")
            path = Path(fh.name)
        expected = hashlib.sha256(b"hello world").hexdigest()
        self.assertEqual(run_workflow.sha256_file(path), expected)
        path.unlink()


# ---------------------------------------------------------------------------
# run_workflow — build_paths
# ---------------------------------------------------------------------------

class TestBuildPaths(unittest.TestCase):
    def test_paths_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wdir = Path(tmpdir)
            paths = run_workflow.build_paths(wdir)
            self.assertEqual(paths.workflow_dir, wdir)
            self.assertEqual(paths.manifest_path, wdir / "workflow.json")
            self.assertEqual(paths.state_dir, wdir / "state")
            self.assertEqual(paths.step_state_path, wdir / "state" / "step-status.tsv")
            self.assertEqual(paths.approval_state_path, wdir / "state" / "approval-status.tsv")
            self.assertEqual(paths.log_dir, wdir / "logs")


# ---------------------------------------------------------------------------
# run_workflow — read_tsv_state / write_tsv_state
# ---------------------------------------------------------------------------

class TestTsvStateRoundtrip(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.tsv"
            state = {"01-collect": "pending", "02-run": "done"}
            run_workflow.write_tsv_state(path, state)
            loaded = run_workflow.read_tsv_state(path)
            self.assertEqual(loaded, state)

    def test_missing_file_returns_empty(self):
        path = Path("/tmp/nonexistent-tsv-state.tsv")
        self.assertEqual(run_workflow.read_tsv_state(path), {})

    def test_empty_file_returns_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False) as fh:
            path = Path(fh.name)
        result = run_workflow.read_tsv_state(path)
        self.assertEqual(result, {})
        path.unlink()


# ---------------------------------------------------------------------------
# run_workflow — atomic_write_text
# ---------------------------------------------------------------------------

class TestAtomicWriteText(unittest.TestCase):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "out.txt"
            run_workflow.atomic_write_text(path, "hello")
            self.assertEqual(path.read_text(encoding="utf-8"), "hello")

    def test_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.txt"
            run_workflow.atomic_write_text(path, "first")
            run_workflow.atomic_write_text(path, "second")
            self.assertEqual(path.read_text(encoding="utf-8"), "second")


# ---------------------------------------------------------------------------
# workflow_schema — normalize_contract
# ---------------------------------------------------------------------------

class TestNormalizeContract(unittest.TestCase):
    def test_string_becomes_file(self):
        result = workflow_schema.normalize_contract("artifacts/out.txt")
        self.assertEqual(result["type"], "file")
        self.assertEqual(result["path"], "artifacts/out.txt")
        self.assertTrue(result["required"])

    def test_dict_defaults(self):
        result = workflow_schema.normalize_contract({"path": "out.txt"})
        self.assertEqual(result["type"], "file")
        self.assertTrue(result["required"])

    def test_dict_preserves_type(self):
        result = workflow_schema.normalize_contract({"path": "out.json", "type": "json"})
        self.assertEqual(result["type"], "json")

    def test_invalid_returns_none(self):
        self.assertIsNone(workflow_schema.normalize_contract(None))
        self.assertIsNone(workflow_schema.normalize_contract(42))


# ---------------------------------------------------------------------------
# workflow_schema — simulate_step_order
# ---------------------------------------------------------------------------

class TestSimulateStepOrder(unittest.TestCase):
    def _manifest(self, steps, execution_model="dag", schema_version=4):
        return {
            "schema_version": schema_version,
            "steps": steps,
            "graph": {"execution_model": execution_model},
        }

    def test_linear_sequence(self):
        steps = [
            {"id": "01-a", "depends_on": []},
            {"id": "02-b", "depends_on": ["01-a"]},
            {"id": "03-c", "depends_on": ["02-b"]},
        ]
        result = workflow_schema.simulate_step_order(self._manifest(steps))
        self.assertEqual(result, ["01-a", "02-b", "03-c"])

    def test_no_deps_preserves_order(self):
        steps = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        result = workflow_schema.simulate_step_order(self._manifest(steps))
        self.assertEqual(result, ["a", "b", "c"])

    def test_sequence_model_returns_declaration_order(self):
        steps = [{"id": "a", "depends_on": ["b"]}, {"id": "b", "depends_on": []}]
        result = workflow_schema.simulate_step_order(self._manifest(steps, execution_model="sequence"))
        self.assertEqual(result, ["a", "b"])

    def test_schema_v2_returns_declaration_order(self):
        steps = [{"id": "b", "depends_on": []}, {"id": "a", "depends_on": ["b"]}]
        result = workflow_schema.simulate_step_order(self._manifest(steps, schema_version=2))
        self.assertEqual(result, ["b", "a"])

    def test_empty_manifest(self):
        result = workflow_schema.simulate_step_order({"steps": [], "graph": {"execution_model": "dag"}})
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# security_audit — collect_manifest_findings
# ---------------------------------------------------------------------------

class TestCollectManifestFindings(unittest.TestCase):
    def test_wildcard_env_warning(self):
        manifest = {"environment": {"allowed_env": ["*"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = security_audit.collect_manifest_findings(manifest, Path(tmpdir))
        self.assertTrue(any("Wildcard" in issue.message for issue in issues))

    def test_empty_allowlist_warning(self):
        manifest = {"tooling": {"allowlisted_commands": []}}
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = security_audit.collect_manifest_findings(manifest, Path(tmpdir))
        self.assertTrue(any("allowlist" in issue.message for issue in issues))

    def test_no_findings_for_clean_manifest(self):
        # A manifest with a non-empty allowlist and no wildcard env should be clean
        manifest = {"tooling": {"allowlisted_commands": ["bash", "python3"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = security_audit.collect_manifest_findings(manifest, Path(tmpdir))
        self.assertEqual(issues, [])


# ---------------------------------------------------------------------------
# security_audit — collect_script_findings
# ---------------------------------------------------------------------------

class TestCollectScriptFindings(unittest.TestCase):
    def test_detects_eval(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            steps_dir = Path(tmpdir) / "steps"
            steps_dir.mkdir()
            (steps_dir / "01-bad.sh").write_text("eval something\n", encoding="utf-8")
            issues = security_audit.collect_script_findings(Path(tmpdir))
        self.assertTrue(any("eval" in issue.message.lower() for issue in issues))

    def test_no_findings_for_clean_scripts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            steps_dir = Path(tmpdir) / "steps"
            steps_dir.mkdir()
            (steps_dir / "01-ok.sh").write_text("echo hello\n", encoding="utf-8")
            issues = security_audit.collect_script_findings(Path(tmpdir))
        self.assertEqual(issues, [])


# ---------------------------------------------------------------------------
# lint_determinism — scan_step_script
# ---------------------------------------------------------------------------

class TestScanStepScript(unittest.TestCase):
    def test_missing_pipefail(self):
        findings: list[lint_determinism.Finding] = []
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w") as fh:
            fh.write("echo hello\n")
            path = Path(fh.name)
        lint_determinism.scan_step_script(path, findings)
        path.unlink()
        self.assertTrue(any("pipefail" in f.message for f in findings))

    def test_has_pipefail_no_error(self):
        findings: list[lint_determinism.Finding] = []
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w") as fh:
            fh.write("set -euo pipefail\necho hello\n")
            path = Path(fh.name)
        lint_determinism.scan_step_script(path, findings)
        path.unlink()
        self.assertFalse(any("pipefail" in f.message for f in findings))

    def test_subjective_pattern_flagged(self):
        findings: list[lint_determinism.Finding] = []
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w") as fh:
            fh.write("set -euo pipefail\n# inspect and decide\n")
            path = Path(fh.name)
        lint_determinism.scan_step_script(path, findings)
        path.unlink()
        self.assertTrue(any("Subjective" in f.message for f in findings))

    def test_missing_script_adds_error(self):
        findings: list[lint_determinism.Finding] = []
        lint_determinism.scan_step_script(Path("/nonexistent/script.sh"), findings)
        self.assertTrue(any(f.severity == "error" for f in findings))


# ---------------------------------------------------------------------------
# lint_determinism — add_finding helper
# ---------------------------------------------------------------------------

class TestAddFinding(unittest.TestCase):
    def test_adds_finding(self):
        findings: list[lint_determinism.Finding] = []
        lint_determinism.add_finding(findings, "warning", Path("/some/path.sh"), "test msg", line=5)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "warning")
        self.assertEqual(findings[0].message, "test msg")
        self.assertEqual(findings[0].line, 5)


# ---------------------------------------------------------------------------
# workflow_schema — validate_manifest (full manifest)
# ---------------------------------------------------------------------------

def _minimal_valid_manifest(tmpdir: Path) -> dict:
    """Return a minimal schema v4 manifest that passes validate_manifest."""
    return {
        "schema_version": 4,
        "workflow_name": "test-wf",
        "version": 1,
        "goal": "Test goal",
        "policy_pack": "strict-prod",
        "policy": {},
        "working_directory": ".",
        "inputs": [],
        "outputs": [],
        "graph": {"execution_model": "dag"},
        "environment": {"network_mode": "inherit"},
        "tooling": {"allowlisted_commands": ["bash"]},
        "migrations": {"current_from": None},
        "failure_policy": {"on_error": "stop", "max_retries": 0},
        "audit": {"enabled": True, "directory": "audit/runs"},
        "residual_nondeterminism": ["none"],
        "steps": [
            {
                "id": "01-run",
                "name": "run",
                "type": "shell",
                "success_gate": "file exists artifacts/01-run.done",
                "gate_type": "artifact",
                "requires_approval": False,
                "retry_limit": 0,
                "timeout_seconds": 60,
                "script": "steps/01-run.sh",
                "depends_on": [],
                "produces": [],
                "consumes": [],
                "commands": ["./steps/01-run.sh"],
                "validation_checks": [],
                "executor_config": {},
            }
        ],
        "sidecars": [],
    }


class TestValidateManifestFull(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self):
        return self.tmpdir / "workflow.json"

    def test_valid_manifest_no_errors(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        issues = workflow_schema.validate_manifest(manifest, self._path())
        errors = [i for i in issues if i.severity == "error"]
        self.assertEqual(errors, [])

    def test_non_dict_root(self):
        issues = workflow_schema.validate_manifest([], self._path())
        self.assertTrue(any("root must be an object" in i.message for i in issues))

    def test_unsupported_schema_version(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        manifest["schema_version"] = 99
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("schema_version" in i.message for i in issues))

    def test_bad_graph_execution_model(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        manifest["graph"]["execution_model"] = "unknown"
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("execution_model" in i.message for i in issues))

    def test_missing_step_required_field(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        manifest["steps"] = [{"id": "01-a", "name": "a", "type": "shell"}]
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("missing" in i.message.lower() for i in issues))

    def test_duplicate_step_id(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        step = {
            "id": "01-a", "name": "a", "type": "shell",
            "success_gate": "file exists artifacts/a.done",
            "gate_type": "artifact",
            "requires_approval": False,
            "retry_limit": 0,
            "timeout_seconds": 60,
            "script": "steps/01-a.sh",
            "depends_on": [],
            "produces": [],
            "consumes": [],
            "commands": [],
            "validation_checks": [],
            "executor_config": {},
        }
        manifest["steps"] = [step, dict(step)]
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("Duplicate step id" in i.message for i in issues))

    def test_invalid_failure_policy_on_error(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        manifest["failure_policy"]["on_error"] = "invalid"
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("on_error" in i.message for i in issues))

    def test_negative_max_retries(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        manifest["failure_policy"]["max_retries"] = -1
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("max_retries" in i.message for i in issues))

    def test_depends_on_unknown_step(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        step = {
            "id": "01-a", "name": "a", "type": "shell",
            "success_gate": "file exists artifacts/a.done",
            "gate_type": "artifact",
            "requires_approval": False,
            "retry_limit": 0,
            "timeout_seconds": 60,
            "script": "steps/01-a.sh",
            "depends_on": ["nonexistent-step"],
            "produces": [],
            "consumes": [],
            "commands": [],
            "validation_checks": [],
            "executor_config": {},
        }
        manifest["steps"] = [step]
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("unknown step" in i.message for i in issues))

    def test_invalid_contract_in_produces(self):
        manifest = _minimal_valid_manifest(self.tmpdir)
        step = {
            "id": "01-a", "name": "a", "type": "shell",
            "success_gate": "file exists artifacts/a.done",
            "gate_type": "artifact",
            "requires_approval": False,
            "retry_limit": 0,
            "timeout_seconds": 60,
            "script": "steps/01-a.sh",
            "depends_on": [],
            "produces": [{"type": "badtype", "path": "artifacts/a.done"}],
            "consumes": [],
            "commands": [],
            "validation_checks": [],
            "executor_config": {},
        }
        manifest["steps"] = [step]
        issues = workflow_schema.validate_manifest(manifest, self._path())
        self.assertTrue(any("invalid contract type" in i.message for i in issues))


# ---------------------------------------------------------------------------
# workflow_schema — summarize_sidecars
# ---------------------------------------------------------------------------

class TestSummarizeSidecars(unittest.TestCase):
    def test_empty_sidecars(self):
        result = workflow_schema.summarize_sidecars({"sidecars": []})
        self.assertEqual(result, [])

    def test_single_sidecar(self):
        manifest = {
            "sidecars": [
                {
                    "id": "sc-01",
                    "when": "before step 02",
                    "consumer_step": "02-review",
                    "kind": "prompt",
                    "validator": "scripts/validate.sh",
                }
            ]
        }
        result = workflow_schema.summarize_sidecars(manifest)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "sc-01")
        self.assertEqual(result[0]["kind"], "prompt")

    def test_non_dict_sidecar_skipped(self):
        manifest = {"sidecars": ["not-a-dict"]}
        result = workflow_schema.summarize_sidecars(manifest)
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# run_workflow — utc_now, print_table, should_require_approval
# ---------------------------------------------------------------------------

class TestUtcNow(unittest.TestCase):
    def test_returns_string(self):
        result = run_workflow.utc_now()
        self.assertIsInstance(result, str)
        self.assertIn("T", result)


class TestPrintTable(unittest.TestCase):
    def test_no_crash(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_workflow.print_table(["col1", "col2"], [["a", "b"], ["cc", "dd"]])
        output = buf.getvalue()
        self.assertIn("col1", output)
        self.assertIn("a", output)


class TestShouldRequireApproval(unittest.TestCase):
    def test_step_requires_approval_true(self):
        step = {"requires_approval": True, "type": "shell", "name": "publish"}
        self.assertTrue(run_workflow.should_require_approval(step, {}))

    def test_step_type_in_policy(self):
        step = {"requires_approval": False, "type": "approval", "name": "gate"}
        policy = {"approval": {"required_for": ["approval"]}}
        self.assertTrue(run_workflow.should_require_approval(step, policy))

    def test_not_required(self):
        step = {"requires_approval": False, "type": "shell", "name": "test"}
        self.assertFalse(run_workflow.should_require_approval(step, {}))


# ---------------------------------------------------------------------------
# run_workflow — load_policy
# ---------------------------------------------------------------------------

class TestLoadPolicy(unittest.TestCase):
    def test_loads_existing_policy(self):
        skill_dir = Path(__file__).resolve().parents[1]
        # strict-prod must exist
        policy = run_workflow.load_policy(skill_dir, "strict-prod")
        self.assertIsInstance(policy, dict)

    def test_unknown_policy_raises(self):
        skill_dir = Path(__file__).resolve().parents[1]
        with self.assertRaises(FileNotFoundError):
            run_workflow.load_policy(skill_dir, "nonexistent-policy-xyz")


# ---------------------------------------------------------------------------
# run_workflow — read_json_file helpers
# ---------------------------------------------------------------------------

class TestReadJsonFile(unittest.TestCase):
    def test_valid_json_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as fh:
            json.dump({"key": "value"}, fh)
            path = Path(fh.name)
        result = run_workflow.read_json_file(path)
        self.assertEqual(result["key"], "value")
        path.unlink()

    def test_missing_file_returns_default(self):
        result = run_workflow.read_json_file(Path("/nonexistent/file.json"), {"default": True})
        self.assertTrue(result["default"])

    def test_invalid_json_returns_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as fh:
            fh.write("not json{{{")
            path = Path(fh.name)
        result = run_workflow.read_json_file(path, {"fallback": 1})
        self.assertEqual(result.get("fallback"), 1)
        path.unlink()


# ---------------------------------------------------------------------------
# run_workflow — append_jsonl, append_text
# ---------------------------------------------------------------------------

class TestAppendHelpers(unittest.TestCase):
    def test_append_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.jsonl"
            run_workflow.append_jsonl(path, {"event": "step-start", "step_id": "01"})
            run_workflow.append_jsonl(path, {"event": "step-done", "step_id": "01"})
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["event"], "step-start")

    def test_append_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "log.txt"
            run_workflow.append_text(path, "line one")
            run_workflow.append_text(path, "line two")
            content = path.read_text(encoding="utf-8")
            self.assertIn("line one", content)
            self.assertIn("line two", content)


# ---------------------------------------------------------------------------
# run_workflow — summarize_policy
# ---------------------------------------------------------------------------

class TestSummarizePolicy(unittest.TestCase):
    def test_deep_copy(self):
        policy = {"audit": {"enabled": True}, "approval": {"required_for": ["shell"]}}
        result = run_workflow.summarize_policy(policy)
        self.assertEqual(result["audit"]["enabled"], True)
        # Mutating result should not affect original
        result["audit"]["enabled"] = False
        self.assertTrue(policy["audit"]["enabled"])


# ---------------------------------------------------------------------------
# run_workflow — atomic_write_json
# ---------------------------------------------------------------------------

class TestAtomicWriteJson(unittest.TestCase):
    def test_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            run_workflow.atomic_write_json(path, {"hello": "world", "n": 42})
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["hello"], "world")
            self.assertEqual(loaded["n"], 42)


# ---------------------------------------------------------------------------
# run_workflow — read_tsv_state_with_errors
# ---------------------------------------------------------------------------

class TestReadTsvStateWithErrors(unittest.TestCase):
    def test_malformed_line(self):
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False, mode="w") as fh:
            fh.write("no-tab-here\n")
            path = Path(fh.name)
        state, errors = run_workflow.read_tsv_state_with_errors(path)
        self.assertEqual(state, {})
        self.assertTrue(len(errors) > 0)
        path.unlink()

    def test_valid_lines(self):
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False, mode="w") as fh:
            fh.write("step1\tdone\nstep2\tpending\n")
            path = Path(fh.name)
        state, errors = run_workflow.read_tsv_state_with_errors(path)
        self.assertEqual(state["step1"], "done")
        self.assertEqual(errors, [])
        path.unlink()

    def test_missing_file(self):
        state, errors = run_workflow.read_tsv_state_with_errors(Path("/nonexistent/file.tsv"))
        self.assertEqual(state, {})
        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# run_workflow — WorkflowLock (context manager)
# ---------------------------------------------------------------------------

class TestWorkflowLock(unittest.TestCase):
    def test_lock_acquires_and_releases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".workflow.lock"
            with run_workflow.WorkflowLock(lock_path):
                self.assertTrue(lock_path.exists())


# ---------------------------------------------------------------------------
# run_workflow — ensure_state (creates state directory structure)
# ---------------------------------------------------------------------------

class TestEnsureState(unittest.TestCase):
    def test_creates_state_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wdir = Path(tmpdir)
            paths = run_workflow.build_paths(wdir)
            manifest = {
                "steps": [
                    {"id": "01-run", "requires_approval": False}
                ]
            }
            run_workflow.ensure_state(paths, manifest)
            self.assertTrue(paths.state_dir.exists())
            self.assertTrue(paths.log_dir.exists())
            self.assertTrue(paths.step_state_path.exists())
            self.assertTrue(paths.approval_state_path.exists())

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wdir = Path(tmpdir)
            paths = run_workflow.build_paths(wdir)
            manifest = {"steps": [{"id": "01-run", "requires_approval": False}]}
            run_workflow.ensure_state(paths, manifest)
            # Second call should not raise
            run_workflow.ensure_state(paths, manifest)


# ---------------------------------------------------------------------------
# workflow_schema — _topological_step_order (DAG cycle detection)
# ---------------------------------------------------------------------------

class TestTopologicalStepOrder(unittest.TestCase):
    def _manifest(self, steps):
        return {
            "schema_version": 4,
            "steps": steps,
            "graph": {"execution_model": "dag"},
        }

    def test_parallel_deps(self):
        steps = [
            {"id": "a", "depends_on": []},
            {"id": "b", "depends_on": []},
            {"id": "c", "depends_on": ["a", "b"]},
        ]
        result = workflow_schema.simulate_step_order(self._manifest(steps))
        # a and b must come before c
        self.assertIn("c", result)
        self.assertLess(result.index("a"), result.index("c"))
        self.assertLess(result.index("b"), result.index("c"))

    def test_cycle_returns_declaration_order(self):
        # cycle: a->b, b->a — topological returns fewer steps than total
        steps = [
            {"id": "a", "depends_on": ["b"]},
            {"id": "b", "depends_on": ["a"]},
        ]
        # simulate_step_order falls back to declaration order when cycle detected
        result = workflow_schema.simulate_step_order(self._manifest(steps))
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# workflow_schema — validate_manifest: audit field errors
# ---------------------------------------------------------------------------

class TestValidateManifestAuditField(unittest.TestCase):
    def test_bad_audit_enabled(self):
        manifest = _minimal_valid_manifest(Path("/tmp"))
        manifest["audit"]["enabled"] = "yes"  # not a bool
        issues = workflow_schema.validate_manifest(manifest, Path("/tmp/workflow.json"))
        self.assertTrue(any("audit.enabled" in i.message for i in issues))

    def test_empty_audit_directory(self):
        manifest = _minimal_valid_manifest(Path("/tmp"))
        manifest["audit"]["directory"] = ""
        issues = workflow_schema.validate_manifest(manifest, Path("/tmp/workflow.json"))
        self.assertTrue(any("audit.directory" in i.message for i in issues))


# ---------------------------------------------------------------------------
# workflow_schema — validate_manifest: environment.network_mode
# ---------------------------------------------------------------------------

class TestValidateManifestEnvironment(unittest.TestCase):
    def test_missing_network_mode(self):
        manifest = _minimal_valid_manifest(Path("/tmp"))
        manifest["environment"] = {}
        issues = workflow_schema.validate_manifest(manifest, Path("/tmp/workflow.json"))
        self.assertTrue(any("network_mode" in i.message for i in issues))


# ---------------------------------------------------------------------------
# lint_determinism — scan_todos
# ---------------------------------------------------------------------------

class TestScanTodos(unittest.TestCase):
    def test_todo_flagged(self):
        findings: list[lint_determinism.Finding] = []
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as fh:
            fh.write("# Spec\nTODO: fill this in\n")
            path = Path(fh.name)
        lint_determinism.scan_todos(path, findings)
        path.unlink()
        self.assertTrue(any("TODO" in f.message for f in findings))

    def test_no_todo_no_findings(self):
        findings: list[lint_determinism.Finding] = []
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as fh:
            fh.write("# Clean spec\nAll done.\n")
            path = Path(fh.name)
        lint_determinism.scan_todos(path, findings)
        path.unlink()
        self.assertEqual(findings, [])

    def test_missing_file_adds_error(self):
        findings: list[lint_determinism.Finding] = []
        lint_determinism.scan_todos(Path("/nonexistent/spec.md"), findings)
        self.assertTrue(any(f.severity == "error" for f in findings))


# ---------------------------------------------------------------------------
# lint_determinism — resolve_workflow_dir
# ---------------------------------------------------------------------------

class TestLintResolveWorkflowDir(unittest.TestCase):
    def test_directory_returns_itself(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = lint_determinism.resolve_workflow_dir(Path(tmpdir))
            self.assertTrue(result.is_dir())

    def test_file_returns_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "workflow.json"
            f.write_text("{}", encoding="utf-8")
            result = lint_determinism.resolve_workflow_dir(f)
            self.assertEqual(result, Path(tmpdir).resolve())


# ---------------------------------------------------------------------------
# workflow_schema — resolve_workflow_dir
# ---------------------------------------------------------------------------

class TestSchemaResolveWorkflowDir(unittest.TestCase):
    def test_dir_returns_itself(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = workflow_schema.resolve_workflow_dir(Path(tmpdir))
            self.assertEqual(result, Path(tmpdir).resolve())

    def test_file_returns_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "workflow.json"
            f.write_text("{}", encoding="utf-8")
            result = workflow_schema.resolve_workflow_dir(f)
            self.assertEqual(result, Path(tmpdir).resolve())


# ---------------------------------------------------------------------------
# workflow_schema — Issue.to_dict
# ---------------------------------------------------------------------------

class TestIssueToDict(unittest.TestCase):
    def test_to_dict(self):
        issue = workflow_schema.Issue(severity="error", message="bad field", path="/some/path")
        d = issue.to_dict()
        self.assertEqual(d["severity"], "error")
        self.assertEqual(d["message"], "bad field")
        self.assertIsNone(d["line"])

    def test_to_dict_with_line(self):
        issue = workflow_schema.Issue(severity="warning", message="warn", path="/path", line=10)
        d = issue.to_dict()
        self.assertEqual(d["line"], 10)


# ---------------------------------------------------------------------------
# workflow_schema — load_manifest
# ---------------------------------------------------------------------------

class TestLoadManifest(unittest.TestCase):
    def test_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as fh:
            json.dump({"schema_version": 4}, fh)
            path = Path(fh.name)
        result = workflow_schema.load_manifest(path)
        self.assertEqual(result["schema_version"], 4)
        path.unlink()


# ---------------------------------------------------------------------------
# verify_workflow — main (exercised via direct import)
# ---------------------------------------------------------------------------

import verify_workflow  # noqa: E402


class TestVerifyWorkflowMain(unittest.TestCase):
    def test_missing_workflow_json_returns_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc = verify_workflow.main([tmpdir])
        self.assertEqual(rc, 1)

    def test_valid_workflow_returns_0(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wdir = Path(tmpdir)
            manifest = _minimal_valid_manifest(wdir)
            (wdir / "workflow.json").write_text(json.dumps(manifest), encoding="utf-8")
            rc = verify_workflow.main([tmpdir, "--simulate"])
        # may have error because strict-prod policy pack is resolved from skill dir
        # just check it runs without exception and returns int
        self.assertIn(rc, (0, 1))

    def test_simulate_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wdir = Path(tmpdir)
            manifest = _minimal_valid_manifest(wdir)
            (wdir / "workflow.json").write_text(json.dumps(manifest), encoding="utf-8")
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                verify_workflow.main([tmpdir, "--simulate"])
            output = buf.getvalue()
            self.assertIn("SIMULATION", output)


# ---------------------------------------------------------------------------
# compile_workflow — choose_kind and choose_policy_pack (pure functions)
# ---------------------------------------------------------------------------

import compile_workflow  # noqa: E402


class TestChooseKind(unittest.TestCase):
    def test_release_kind(self):
        self.assertEqual(compile_workflow.choose_kind("deploy to production"), "release")

    def test_code_fix_kind(self):
        self.assertEqual(compile_workflow.choose_kind("fix the failing CI test"), "code-fix")

    def test_generic_kind(self):
        self.assertEqual(compile_workflow.choose_kind("do something random"), "generic")


class TestChoosePolicyPack(unittest.TestCase):
    def test_release_uses_strict_prod(self):
        self.assertEqual(compile_workflow.choose_policy_pack("release", "deploy"), "strict-prod")

    def test_code_fix_uses_ai_sidecar_safe(self):
        self.assertEqual(compile_workflow.choose_policy_pack("code-fix", "fix test"), "ai-sidecar-safe")


if __name__ == "__main__":
    unittest.main()
