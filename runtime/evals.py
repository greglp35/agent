from __future__ import annotations
from pathlib import Path
from typing import Any, Callable
import json
from .engine import compile_command, run_semantic
from .adapters.mock import DeterministicLLMAdapter


class EvaluationHarness:
    def __init__(self, cases: list[dict[str, Any]]):
        self.cases=cases

    @classmethod
    def from_json(cls, path: str | Path):
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["cases"] if isinstance(data,dict) else data)

    def run(self, llm_factory: Callable[[], Any] | None = None) -> dict[str, Any]:
        llm_factory=llm_factory or DeterministicLLMAdapter
        results=[]
        for case in self.cases:
            compiled=compile_command(case["input"], source=case.get("source","user"))
            errors=[]
            expect=case.get("expect",{})
            if "commands" in expect:
                for cmd in expect["commands"]:
                    if cmd not in compiled["ir"].get("commands",[]):
                        errors.append(f"missing command:{cmd}")
            if "depth" in expect and compiled["ir"].get("depth") != expect["depth"]:
                errors.append(f"depth:{compiled['ir'].get('depth')} != {expect['depth']}")
            if case.get("semantic",False) and case.get("source","user") == "user":
                run=run_semantic(case["input"], llm_factory())
                wanted=expect.get("execution_status","EXECUTED")
                if run["execution"].get("execution_status") != wanted:
                    errors.append(f"execution:{run['execution'].get('execution_status')} != {wanted}")
            results.append({"id":case.get("id"),"pass":not errors,"errors":errors})
        passed=sum(1 for r in results if r["pass"])
        return {"total":len(results),"passed":passed,"failed":len(results)-passed,"results":results}
