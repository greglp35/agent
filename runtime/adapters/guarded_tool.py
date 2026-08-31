from __future__ import annotations
from typing import Any
from ..production import ApprovalGate, ExecutionJournal


def infer_effect(capability: str) -> str:
    c = capability.lower()
    if "delete" in c or "destructive" in c:
        return "destructive"
    if c in {"deploy.production", "production.deploy"}:
        return "production_deploy"
    if c.endswith(".write") or c.endswith(".send") or c.endswith(".commit") or c.endswith(".merge"):
        return "write"
    if c.endswith(".read") or c.endswith(".search") or c.endswith(".fetch"):
        return "read"
    return "external_side_effect"


class GuardedToolAdapter:
    def __init__(self, inner, *, effect: str | None = None, approval_gate: ApprovalGate | None = None,
                 journal: ExecutionJournal | None = None):
        self.inner = inner
        self.capability = inner.capability
        self.effect = effect or getattr(inner, "effect", None) or infer_effect(self.capability)
        self.approval_gate = approval_gate or ApprovalGate()
        self.journal = journal

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.approval_gate.require(self.effect, {"capability":self.capability,"arguments":arguments})
        try:
            result = self.inner.invoke(arguments)
            if self.journal:
                self.journal.append({"type":"tool_call","capability":self.capability,"effect":self.effect,
                                     "status":"EXECUTED","arguments":arguments,"result":result})
            return result
        except Exception as exc:
            if self.journal:
                self.journal.append({"type":"tool_call","capability":self.capability,"effect":self.effect,
                                     "status":"BLOCKED","arguments":arguments,"error":str(exc)})
            raise
