import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


COMMANDS = load("registry/commands.json")["commands"]
METHODS = load("registry/methods.json")["methods"]
MODIFIERS = load("registry/modifiers.json")["modifiers"]
EXPERTS = load("experts/expert-registry.json")["experts"]


class RegistryInvariantTests(unittest.TestCase):
    pass


def command_test(item):
    def test(self):
        self.assertRegex(item["name"], r"^[a-z][a-z0-9_-]*$")
        self.assertIn(item["class"], {"role_router","acquisition","reasoning","operation","execution","presentation","continuity"})
        self.assertIn(item["default_depth"], {"FAST","STANDARD","DEEP","FORENSIC"})
        self.assertTrue(item["mission"].strip())
        self.assertIsInstance(item["default_output"], list)
    return test


def method_test(item):
    def test(self):
        self.assertRegex(item["name"], r"^[a-z][a-z0-9_-]*$")
        self.assertTrue(item["mission"].strip())
        self.assertGreaterEqual(len(item["steps"]), 2)
        self.assertEqual(len(item["steps"]), len(set(item["steps"])))
    return test


def modifier_test(item):
    def test(self):
        self.assertRegex(item["name"], r"^[a-z][a-z0-9_-]*$")
        self.assertTrue(item["category"])
        self.assertTrue(any(k in item for k in ("effect","value","expects_value")))
    return test


def expert_test(item):
    def test(self):
        self.assertRegex(item["id"], r"^[a-z][a-z0-9_]*$")
        self.assertTrue(item["domain"])
        self.assertTrue(item["mission"])
        for key in ("standards","questions","failure_modes","keywords"):
            self.assertIsInstance(item[key], list)
            self.assertGreaterEqual(len(item[key]), 3)
    return test


for i, item in enumerate(COMMANDS):
    setattr(RegistryInvariantTests, f"test_command_{i:03d}_{item['name'].replace('-', '_')}", command_test(item))
for i, item in enumerate(METHODS):
    setattr(RegistryInvariantTests, f"test_method_{i:03d}_{item['name'].replace('-', '_')}", method_test(item))
for i, item in enumerate(MODIFIERS):
    setattr(RegistryInvariantTests, f"test_modifier_{i:03d}_{item['name'].replace('-', '_')}", modifier_test(item))
for i, item in enumerate(EXPERTS):
    setattr(RegistryInvariantTests, f"test_expert_{i:03d}_{item['id']}", expert_test(item))
