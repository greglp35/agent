import json, tempfile, unittest, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime import compile_command, run_command
from runtime.capabilities import resolve_capabilities
from runtime.state import StateStore
from runtime.trace import TraceLogger

class Alpha3Tests(unittest.TestCase):
    def test_default_missing_llm(self):
        c = compile_command("/audit mon application")
        self.assertIn("llm.reason", resolve_capabilities(c["ir"])["missing_required"])

    def test_provided_llm(self):
        c = compile_command("/audit mon application")
        self.assertTrue(resolve_capabilities(c["ir"], {"llm.reason":True})["can_execute_semantically"])

    def test_web_missing(self):
        c = compile_command("/research réglementation --web")
        caps = resolve_capabilities(c["ir"], {"llm.reason":True, "web.search":False})
        self.assertIn("web.search", caps["missing_required"])

    def test_web_available(self):
        c = compile_command("/research réglementation --web")
        caps = resolve_capabilities(c["ir"], {"llm.reason":True, "web.search":True})
        self.assertTrue(caps["can_execute_semantically"])

    def test_dry_run(self):
        r = run_command("/audit mon application", dry_run=True)
        self.assertEqual(r["execution"]["execution_status"], "SIMULATED")

    def test_no_adapter(self):
        r = run_command("/audit mon application", provided_capabilities={"llm.reason":True}, dry_run=False)
        self.assertEqual(r["execution"]["execution_status"], "NOT_AVAILABLE")

    def test_adapter_execution(self):
        def adapter(step): return {"status":"EXECUTED","verdict":"ok"}
        r = run_command("/audit mon application", provided_capabilities={"llm.reason":True},
                        adapters={"audit":adapter}, dry_run=False)
        self.assertEqual(r["execution"]["execution_status"], "EXECUTED")

    def test_adapter_blocked(self):
        def adapter(step): raise RuntimeError("boom")
        r = run_command("/audit mon application", provided_capabilities={"llm.reason":True},
                        adapters={"audit":adapter}, dry_run=False)
        self.assertEqual(r["execution"]["execution_status"], "BLOCKED")

    def test_state_store(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"state.json"
            s = StateStore(p)
            s.update(active_project="command-os", current_task="runtime")
            self.assertEqual(StateStore(p).load()["current_task"], "runtime")

    def test_trace(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"trace.jsonl"
            TraceLogger(p).append({"type":"test"})
            self.assertEqual(len(p.read_text(encoding="utf-8").splitlines()), 1)

    def test_quality_execution_status(self):
        r = run_command("/build prototype --forensic", dry_run=True)
        checks = {x["check"]:x["status"] for x in r["execution"]["quality_gate"]["checks"]}
        self.assertEqual(checks["execution_status"], "PASS")
        self.assertIn("confidence", checks)

if __name__ == "__main__":
    unittest.main()
