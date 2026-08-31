import json,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from runtime.policy_packs import Actor,PolicyEngine,load_policy_pack
CASES=json.loads((ROOT/"tests/policy-matrix.json").read_text(encoding="utf-8"))["cases"]
class PolicyMatrixTests(unittest.TestCase): pass

def make_test(case):
    def test(self):
        e=PolicyEngine(load_policy_pack("default")); a=Actor(case["role"],(case["role"],))
        self.assertEqual(e.decide(a,capability=case["capability"],effect=case["effect"]).allowed,case["allowed"])
    return test
for i,case in enumerate(CASES): setattr(PolicyMatrixTests,f"test_policy_{i:03d}",make_test(case))
