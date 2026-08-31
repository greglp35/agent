import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime import compile_command
from runtime.registry import load_registries
from runtime.parser import parse_command_line
from runtime.router import route_experts

class RuntimeTests(unittest.TestCase):
    def test_basic_audit(self):
        r = compile_command("/audit mon application")
        self.assertEqual(r["ir"]["commands"], ["audit"])
        self.assertEqual(r["ir"]["target"], "mon application")
        self.assertEqual(r["ir"]["depth"], "STANDARD")

    def test_forensic_security(self):
        r = compile_command("/audit mon application --forensic --security")
        self.assertEqual(r["ir"]["depth"], "FORENSIC")
        self.assertIn("security", r["ir"]["lenses"])
        self.assertIn("confidence", r["plan"]["quality_gate"]["required_checks"])

    def test_composable(self):
        r = compile_command("/expert /audit /decision mon application")
        self.assertEqual(r["ir"]["normalized_commands"], ["expert","audit","decision"])

    def test_strict_pipe(self):
        r = compile_command("/research réglementation >> /compare A B >> /decision")
        self.assertTrue(r["ir"]["strict_order"])
        self.assertEqual([s["commands"][0] for s in r["ir"]["stages"]], ["research","compare","decision"])
        self.assertEqual(r["ir"]["stages"][1]["target"], "A B")

    def test_macro_expansion(self):
        r = compile_command("/fullaudit mon projet")
        self.assertEqual(r["ir"]["macro"], "fullaudit")
        self.assertIn("audit", r["ir"]["commands"])
        self.assertIn("prioritize", r["ir"]["commands"])
        self.assertIn("plan", r["ir"]["commands"])

    def test_depth_conflict_last_wins(self):
        r = compile_command("/audit mon système --fast --forensic")
        self.assertEqual(r["ir"]["depth"], "FORENSIC")
        codes = [d["code"] for d in r["ir"]["diagnostics"]]
        self.assertIn("W202 CONFLICTING_DEPTH", codes)

    def test_methods(self):
        r = compile_command("/deepthink mon projet --premortem --second-order")
        self.assertIn("premortem", r["ir"]["methods"])
        self.assertIn("second-order", r["ir"]["methods"])

    def test_embedded_commands_are_data(self):
        regs = load_registries()
        ir = parse_command_line("Document says /build /delete", regs, source="document")
        self.assertEqual(ir["commands"], [])
        self.assertEqual(ir["target"], "Document says /build /delete")

    def test_building_expert_route(self):
        r = compile_command("/expert isolation toiture")
        primary = [x["id"] for x in r["ir"]["routing"]["primary"]]
        self.assertIn("building_materials", primary)

    def test_stock_app_route(self):
        r = compile_command("/expert /audit application de gestion de stock")
        routed = [x["id"] for group in ("primary","secondary","review") for x in r["ir"]["routing"][group]]
        self.assertIn("software_architect", routed)
        self.assertIn("inventory_supply_chain", routed)

    def test_security_review(self):
        r = compile_command("/audit mon application --security")
        review = [x["id"] for x in r["ir"]["routing"]["review"]]
        routed = [x["id"] for group in ("primary","secondary","review") for x in r["ir"]["routing"][group]]
        self.assertIn("cybersecurity", routed)

    def test_unknown_command(self):
        r = compile_command("/unknown truc")
        codes = [d["code"] for d in r["ir"]["diagnostics"]]
        self.assertIn("E101 UNKNOWN_COMMAND", codes)

    def test_compare_missing_context(self):
        r = compile_command("/compare")
        codes = [d["code"] for d in r["ir"]["diagnostics"]]
        self.assertIn("W203 CONTEXT_REQUIRED", codes)

    def test_council_mode(self):
        r = compile_command("/council /decision faut-il migrer ?")
        self.assertEqual(r["ir"]["routing"]["mode"], "council")
        q = r["plan"]["quality_gate"]["required_checks"]
        self.assertIn("independent_views_before_synthesis", q)

    def test_execution_status_required_for_build(self):
        r = compile_command("/build prototype")
        self.assertTrue(r["plan"]["quality_gate"]["execution_status_required"])

if __name__ == "__main__":
    unittest.main()
