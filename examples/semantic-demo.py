from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime import run_semantic
from runtime.adapters import DeterministicLLMAdapter


class DemoWebSearch:
    capability = "web.search"

    def invoke(self, arguments):
        return {
            "query": arguments["query"],
            "results": [
                {"title": "Synthetic source", "url": "https://example.invalid", "note": "demo only"}
            ]
        }


llm = DeterministicLLMAdapter()
result = run_semantic(
    "/council /research /decision mon architecture --forensic --web --security",
    llm,
    tool_adapters={"web.search": DemoWebSearch()},
    council_parallel=True,
)

print(result["execution"]["execution_status"])
print(result["execution"]["quality_gate"])
print(result["execution"]["final_output"])
