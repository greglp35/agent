import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime import compile_command, run_semantic
from runtime.adapters import CallableLLMAdapter, DeterministicLLMAdapter, LLMResponse
from runtime.continuity import resolve_continuity


class FakeWeb:
    capability = "web.search"
    def __init__(self): self.calls = []
    def invoke(self, arguments):
        self.calls.append(arguments)
        return {"results":[{"title":"test"}], "query":arguments.get("query")}


class Alpha4Tests(unittest.TestCase):
    def test_semantic_audit_executes(self):
        r = run_semantic("/audit mon application", DeterministicLLMAdapter())
        self.assertEqual(r["execution"]["execution_status"], "EXECUTED")

    def test_semantic_quality_epistemic_passes(self):
        r = run_semantic("/audit mon application", DeterministicLLMAdapter())
        checks = {x["check"]:x["status"] for x in r["execution"]["quality_gate"]["checks"]}
        self.assertEqual(checks["truthfulness_and_evidence"], "PASS")

    def test_forensic_confidence_passes(self):
        r = run_semantic("/audit mon application --forensic", DeterministicLLMAdapter())
        checks = {x["check"]:x["status"] for x in r["execution"]["quality_gate"]["checks"]}
        self.assertEqual(checks["confidence"], "PASS")
        self.assertEqual(checks["root_causes"], "PASS")
        self.assertEqual(checks["failure_scenarios"], "PASS")

    def test_council_preserves_independent_views(self):
        llm = DeterministicLLMAdapter()
        r = run_semantic("/council /decision application de gestion de stock", llm)
        council = next(x for x in r["execution"]["steps"] if x.get("command") == "council")
        self.assertGreaterEqual(len(council["content"]["independent_views"]), 2)

    def test_council_quality_passes(self):
        r = run_semantic("/council /decision application de gestion de stock", DeterministicLLMAdapter())
        checks = {x["check"]:x["status"] for x in r["execution"]["quality_gate"]["checks"]}
        self.assertEqual(checks["independent_views_before_synthesis"], "PASS")
        self.assertEqual(checks["surface_material_disagreements"], "PASS")

    def test_council_parallel_when_host_thread_safe(self):
        r = run_semantic("/council /decision application de gestion de stock", DeterministicLLMAdapter(), council_parallel=True)
        council = next(x for x in r["execution"]["steps"] if x.get("command") == "council")
        self.assertTrue(council["content"]["council_meta"]["parallel"])

    def test_web_tool_context_is_real_adapter_output(self):
        web = FakeWeb()
        r = run_semantic("/research réglementation --web", DeterministicLLMAdapter(), tool_adapters={"web.search":web})
        research = next(x for x in r["execution"]["steps"] if x.get("command") == "research")
        self.assertIn("web.search", research["tool_context_used"])
        self.assertEqual(len(web.calls), 1)

    def test_tool_capability_auto_declared(self):
        web = FakeWeb()
        r = run_semantic("/research réglementation --web", DeterministicLLMAdapter(), tool_adapters={"web.search":web})
        self.assertTrue(r["execution"]["capabilities"]["available"]["web.search"])

    def test_continuity_next_uses_state(self):
        step = {"command":"next", "target":None}
        out = resolve_continuity(step, {"next_action":"run tests"})
        self.assertEqual(out["target"], "run tests")

    def test_continuity_continue_uses_current_task(self):
        step = {"command":"continue", "target":None}
        out = resolve_continuity(step, {"current_task":"semantic runtime"})
        self.assertEqual(out["target"], "semantic runtime")

    def test_semantic_next_with_state_executes(self):
        r = run_semantic("/next", DeterministicLLMAdapter(), state={"next_action":"write adapter tests"})
        step = next(x for x in r["execution"]["steps"] if x.get("command") == "next")
        self.assertEqual(step["status"], "EXECUTED")

    def test_semantic_next_without_state_blocks(self):
        r = run_semantic("/next", DeterministicLLMAdapter())
        step = next(x for x in r["execution"]["steps"] if x.get("command") == "next")
        self.assertEqual(step["status"], "BLOCKED")

    def test_callable_adapter(self):
        def host(req):
            return {
                "summary":"ok",
                "outputs":{},
                "epistemic":{"facts":[],"inferences":[],"assumptions":[],"unknowns":[]},
                "confidence":{"level":"high","reason":"test"}
            }
        r = run_semantic("/audit cible", CallableLLMAdapter(host))
        self.assertEqual(r["execution"]["execution_status"], "EXECUTED")

    def test_callable_adapter_accepts_llmresponse(self):
        def host(req):
            return LLMResponse(content={
                "summary":"ok", "outputs":{},
                "epistemic":{"facts":[],"inferences":[],"assumptions":[],"unknowns":[]},
                "confidence":{"level":"high","reason":"test"}
            })
        r = run_semantic("/audit cible", CallableLLMAdapter(host))
        self.assertEqual(r["execution"]["execution_status"], "EXECUTED")

    def test_previous_output_chains_between_commands(self):
        llm = DeterministicLLMAdapter()
        run_semantic("/audit /decision cible", llm)
        command_requests = [x for x in llm.requests if x.purpose == "command_execution"]
        self.assertGreaterEqual(len(command_requests), 2)
        self.assertIn("previous_outputs", command_requests[1].user)

    def test_expert_specs_injected(self):
        llm = DeterministicLLMAdapter()
        run_semantic("/expert /audit application de gestion de stock", llm)
        request = next(x for x in llm.requests if x.purpose == "command_execution")
        self.assertIn("inventory_supply_chain", request.system)

    def test_council_experts_do_not_receive_other_views(self):
        llm = DeterministicLLMAdapter()
        run_semantic("/council /decision application de gestion de stock", llm)
        view_requests = [x for x in llm.requests if x.purpose == "council_expert_view"]
        self.assertGreaterEqual(len(view_requests), 2)
        self.assertTrue(all("independent_views" not in r.user for r in view_requests))

    def test_council_arbitration_receives_views(self):
        llm = DeterministicLLMAdapter()
        run_semantic("/council /decision application de gestion de stock", llm)
        arbiter = next(x for x in llm.requests if x.purpose == "council_arbitration")
        self.assertIn("independent_views", arbiter.user)

    def test_semantic_result_has_final_output(self):
        r = run_semantic("/decision A ou B", DeterministicLLMAdapter())
        self.assertIsNotNone(r["execution"]["final_output"])

    def test_host_name_exposed(self):
        r = run_semantic("/audit cible", DeterministicLLMAdapter())
        self.assertEqual(r["execution"]["host"], "deterministic-test-host")


if __name__ == "__main__":
    unittest.main()
