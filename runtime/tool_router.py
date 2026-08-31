from __future__ import annotations

from typing import Any, Dict


class ToolRouter:
    """Host-neutral, explicit tool-context acquisition.

    Alpha.4 deliberately keeps tool execution outside the LLM. The host registers
    capability adapters such as ``web.search``. COMMAND OS invokes only adapters
    explicitly requested by the compiled command and returns their raw result to
    the semantic prompt as tool context.
    """

    def __init__(self, adapters: Dict[str, Any] | None = None):
        self.adapters = adapters or {}

    def acquire(self, ir: Dict[str, Any], step: Dict[str, Any]) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        requested = set(ir.get("tool_intents", []))

        if "web" in requested and "web.search" in self.adapters:
            context["web.search"] = self.adapters["web.search"].invoke({
                "query": step.get("target") or ir.get("target"),
                "command": step.get("command"),
                "depth": step.get("depth"),
            })

        return context
