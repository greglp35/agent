import json,tempfile,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from runtime.policy_packs import Actor,PolicyEngine,PolicyApprovalGate,load_policy_pack
from runtime.production import ApprovalRequired
from runtime.api_service import CommandOSAPI,StaticTokenAuthenticator
from runtime.adapters.mock import DeterministicLLMAdapter
from runtime.observability import MetricsRegistry
from runtime.provider_registry import ProviderRegistry
from runtime.baseline import CrossProviderBaseline
from runtime.evals import EvaluationHarness

class DummyTool:
    def __init__(self,capability,effect=None): self.capability=capability; self.effect=effect
    def invoke(self,args): return {"ok":True,"args":args}

class Beta1Tests(unittest.TestCase):
    def setUp(self):
        self.pack=load_policy_pack("default"); self.engine=PolicyEngine(self.pack)
        self.viewer=Actor("viewer-1",("viewer",)); self.analyst=Actor("analyst-1",("analyst",)); self.operator=Actor("operator-1",("operator",)); self.admin=Actor("admin-1",("administrator",))
    def test_viewer_compile_allowed(self): self.assertTrue(self.engine.decide(self.viewer,capability="local.compile",effect="read").allowed)
    def test_viewer_llm_denied(self): self.assertFalse(self.engine.decide(self.viewer,capability="llm.reason",effect="read").allowed)
    def test_analyst_inherits_compile(self): self.assertTrue(self.engine.decide(self.analyst,capability="local.compile",effect="read").allowed)
    def test_analyst_llm_allowed(self): self.assertTrue(self.engine.decide(self.analyst,capability="llm.reason",effect="read").allowed)
    def test_operator_write_requires_approval(self): self.assertTrue(self.engine.decide(self.operator,capability="files.write",effect="write").approval_required)
    def test_operator_can_approve_write(self): self.assertTrue(self.engine.can_approve(self.operator,"write"))
    def test_admin_wildcard_capability(self): self.assertTrue(self.engine.decide(self.admin,capability="deploy.production",effect="production_deploy").allowed)
    def test_same_admin_cannot_self_approve_prod(self):
        with self.assertRaises(ApprovalRequired): self.engine.authorize(self.admin,capability="deploy.production",effect="production_deploy",approver=self.admin)
    def test_second_admin_can_approve_prod(self):
        other=Actor("admin-2",("administrator",)); self.assertTrue(self.engine.authorize(self.admin,capability="deploy.production",effect="production_deploy",approver=other).allowed)
    def test_unknown_role_denied(self): self.assertFalse(self.engine.decide(Actor("x",("missing",)),capability="local.compile",effect="read").allowed)
    def test_locked_down_has_no_operator(self): self.assertFalse(PolicyEngine(load_policy_pack("locked-down")).decide(Actor("x",("operator",)),capability="files.write",effect="write").allowed)
    def test_auth_rejects_missing(self):
        a=StaticTokenAuthenticator({"tok":{"subject":"u","roles":["viewer"]}})
        with self.assertRaises(Exception): a.authenticate({})
    def test_auth_accepts_token(self): self.assertEqual(StaticTokenAuthenticator({"tok":{"subject":"u","roles":["viewer"]}}).authenticate({"authorization":"Bearer tok"}).subject,"u")
    def _api(self):
        auth=StaticTokenAuthenticator({"v":{"subject":"v","roles":["viewer"]},"a":{"subject":"a","roles":["analyst"]},"o":{"subject":"o","roles":["operator"]},"z":{"subject":"z","roles":["administrator"]}})
        return CommandOSAPI(providers={"mock":DeterministicLLMAdapter},authenticator=auth,eval_cases=json.loads((ROOT/"tests/beta1-eval-corpus.json").read_text())["cases"])
    def test_health_public(self): self.assertEqual(self._api().handle("GET","/health").status,200)
    def test_metrics_public(self): self.assertEqual(self._api().handle("GET","/metrics").content_type.split(';')[0],"text/plain")
    def test_compile_requires_auth(self): self.assertEqual(self._api().handle("POST","/v1/compile",{"command":"/audit x"}).status,401)
    def test_compile_viewer(self): self.assertEqual(self._api().handle("POST","/v1/compile",{"command":"/audit x"},{"authorization":"Bearer v"}).status,200)
    def test_run_viewer_forbidden(self): self.assertEqual(self._api().handle("POST","/v1/run",{"command":"/audit x","provider":"mock"},{"authorization":"Bearer v"}).status,403)
    def test_run_analyst(self): self.assertEqual(self._api().handle("POST","/v1/run",{"command":"/audit x","provider":"mock"},{"authorization":"Bearer a"}).status,200)
    def test_run_unknown_provider(self): self.assertEqual(self._api().handle("POST","/v1/run",{"command":"/audit x","provider":"none"},{"authorization":"Bearer a"}).status,400)
    def test_evaluate(self):
        r=self._api().handle("POST","/v1/evaluate",{"providers":["mock"]},{"authorization":"Bearer a"}); self.assertEqual(r.status,200); self.assertEqual(r.body["providers"]["mock"]["failed"],0)
    def test_metrics_after_request(self):
        api=self._api(); api.handle("GET","/health"); self.assertIn("command_os_runs_total",api.handle("GET","/metrics").body)
    def test_provider_names(self): self.assertEqual(ProviderRegistry.from_default().names(),["anthropic","openai"])
    def test_provider_requires_model(self):
        with self.assertRaises(ValueError): ProviderRegistry.from_default().build("openai",env={"OPENAI_API_KEY":"x"})
    def test_unknown_provider_registry(self):
        with self.assertRaises(KeyError): ProviderRegistry.from_default().build("missing",env={})
    def test_baseline_ranking(self):
        h=EvaluationHarness([{"id":"x","input":"/audit x","expect":{"commands":["audit"]}}]); self.assertEqual(set(CrossProviderBaseline(h).run({"a":DeterministicLLMAdapter,"b":DeterministicLLMAdapter})["ranking"]),{"a","b"})
    def test_policy_gate_denies_viewer_write(self):
        with self.assertRaises(PermissionError): PolicyApprovalGate(self.engine,self.viewer,self.admin).require("write",{"capability":"files.write"})
    def test_policy_gate_operator_with_approver(self): PolicyApprovalGate(self.engine,self.operator,self.admin).require("write",{"capability":"files.write"})
    def test_policy_cycle_detected(self):
        from runtime.policy_packs import PolicyPack
        with self.assertRaises(ValueError): PolicyPack({"id":"x","roles":{"a":{"inherits":["b"]},"b":{"inherits":["a"]}}}).permissions_for(Actor("x",("a",)))
    def test_prometheus_render(self):
        m=MetricsRegistry(); m.inc("x_total",role="a"); self.assertIn('x_total{role="a"} 1.0',m.render_prometheus())
    def test_eval_corpus_is_semantic(self): self.assertTrue(all(c.get("semantic") for c in json.loads((ROOT/"tests/beta1-eval-corpus.json").read_text())["cases"]))
    def test_packaged_policy_copy_matches(self): self.assertEqual((ROOT/"policies/default.json").read_text(),(ROOT/"runtime/data/policies/default.json").read_text())
    def test_packaged_provider_copy_matches(self): self.assertEqual((ROOT/"registry/providers.json").read_text(),(ROOT/"runtime/data/registry/providers.json").read_text())
