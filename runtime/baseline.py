from __future__ import annotations
from typing import Any, Callable
import time
from .evals import EvaluationHarness

class CrossProviderBaseline:
    def __init__(self, harness: EvaluationHarness): self.harness=harness
    def run(self, factories: dict[str,Callable[[],Any]]) -> dict[str,Any]:
        providers={}
        for name,factory in factories.items():
            started=time.monotonic(); report=self.harness.run(factory); latency=(time.monotonic()-started)*1000.0
            providers[name]={"total":report["total"],"passed":report["passed"],"failed":report["failed"],
                             "pass_rate":0.0 if not report["total"] else round(report["passed"]/report["total"],4),
                             "latency_ms":round(latency,3),"results":report["results"]}
        ranking=sorted(providers,key=lambda n:(-providers[n]["pass_rate"],providers[n]["latency_ms"],n))
        return {"providers":providers,"ranking":ranking}
