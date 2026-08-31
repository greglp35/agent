import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from runtime import compile_command
from runtime.registry import load_registries


class GregProfileTests(unittest.TestCase):
    def test_profile_is_registered(self):
        self.assertIn("greg",load_registries()["profiles"])

    def test_shortcut_applies_profile(self):
        r=compile_command("/greg /decision mon choix")
        ir=r["ir"]
        self.assertEqual(ir["profile"]["id"],"greg")
        self.assertEqual(ir["depth"],"DEEP")
        self.assertIn("tradeoffs",ir["methods"])
        self.assertIn("reversibility",ir["methods"])
        self.assertIn("terrain",ir["lenses"])
        self.assertIn("strategic",ir["lenses"])

    def test_explicit_depth_wins(self):
        r=compile_command("/greg /audit mon projet --fast")
        self.assertEqual(r["ir"]["depth"],"FAST")

    def test_canonical_profile_modifier(self):
        r=compile_command("/debug bug import --profile=greg")
        self.assertEqual(r["ir"]["profile"]["id"],"greg")
        self.assertEqual(r["ir"]["depth"],"DEEP")
        self.assertIn("rootcause",r["ir"]["methods"])

    def test_write_stays_lightweight(self):
        r=compile_command("/greg /write un mail professionnel")
        self.assertEqual(r["ir"]["depth"],"STANDARD")
        self.assertTrue(r["ir"]["output_preferences"]["no-fluff"])
        self.assertNotIn("terrain",r["ir"]["lenses"])

    def test_plan_propagates_profile(self):
        r=compile_command("/greg /architect mon application")
        steps=[s for s in r["plan"]["steps"] if s.get("command")=="architect"]
        self.assertEqual(steps[0]["profile"]["id"],"greg")
        self.assertTrue(steps[0]["output_preferences"]["actions"])

    def test_shortcut_preserves_original_input(self):
        r=compile_command("/greg /audit mon application")
        self.assertEqual(r["ir"]["raw_input"],"/greg /audit mon application")
        self.assertIn("--profile=greg",r["ir"]["expanded_input"])


if __name__=="__main__": unittest.main()
