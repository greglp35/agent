from __future__ import annotations
from typing import Any, Dict


class ToolRouter:
    """Explicit host tool router. Tools execute outside the LLM."""
    def __init__(self, adapters: Dict[str, Any] | None = None):
        self.adapters = adapters or {}

    def available(self) -> list[str]:
        return sorted(self.adapters.keys())

    def _invoke(self, capability: str, arguments: dict[str, Any]) -> dict[str, Any]:
        adapter=self.adapters[capability]
        return adapter.invoke(arguments)

    def acquire(self, ir: Dict[str, Any], step: Dict[str, Any]) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        requested=set(ir.get("tool_intents", []))
        canonical=[]
        for item in requested:
            canonical.append("web.search" if item == "web" else item)
        for capability in canonical:
            adapter=self.adapters.get(capability)
            if not adapter:
                continue
            effect=getattr(adapter,"effect",None)
            if effect is None:
                effect="read" if capability.endswith((".read",".search",".fetch")) else "external_side_effect"
            if effect != "read":
                continue
            context[capability]=self._invoke(capability,{
                "query":step.get("target") or ir.get("target"),
                "command":step.get("command"),"depth":step.get("depth")})
        return context

    def execute_requests(self, requests: list[dict[str, Any]] | None, *, step: dict[str, Any]) -> list[dict[str, Any]]:
        results=[]
        for req in requests or []:
            capability=req.get("capability")
            arguments=req.get("arguments") if isinstance(req.get("arguments"),dict) else {}
            if not capability or capability not in self.adapters:
                results.append({"capability":capability,"status":"NOT_AVAILABLE"})
                continue
            try:
                value=self._invoke(capability,{**arguments,"command":step.get("command"),"target":step.get("target")})
                results.append({"capability":capability,"status":"EXECUTED","result":value})
            except Exception as exc:
                results.append({"capability":capability,"status":"BLOCKED","error":str(exc)})
        return results
