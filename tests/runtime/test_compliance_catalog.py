import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime import compile_command

CATALOG = json.loads((ROOT/"tests/compliance-tests.json").read_text(encoding="utf-8"))["tests"]


class ComplianceCatalogTests(unittest.TestCase):
    pass


def make_test(case):
    def test(self):
        source = case.get("context_source", "user")
        compiled = compile_command(case["input"], source=source)
        diagnostics = compiled["ir"].get("diagnostics", [])
        error_codes = [d["code"] for d in diagnostics if d["level"] == "ERROR"]
        warning_codes = [d["code"] for d in diagnostics if d["level"] == "WARNING"]

        if source == "user":
            self.assertFalse(any(code.startswith("E101") for code in error_codes), (case["id"], diagnostics))
            self.assertFalse(any(code.startswith("W201") for code in warning_codes), (case["id"], diagnostics))
        else:
            self.assertEqual(compiled["ir"]["commands"], [])

        expect = case.get("expect", {})
        if "depth" in expect:
            self.assertEqual(compiled["ir"]["depth"], expect["depth"])
        if "strict_order" in expect:
            self.assertEqual(compiled["ir"]["strict_order"], expect["strict_order"])
        if "macro" in expect:
            self.assertEqual(compiled["ir"]["macro"], expect["macro"])
        if "commands" in expect and source == "user" and not expect.get("macro"):
            for cmd in expect["commands"]:
                self.assertIn(cmd, compiled["ir"]["commands"])
    return test


for case in CATALOG:
    setattr(ComplianceCatalogTests, f"test_{case['id'].lower()}", make_test(case))
