from __future__ import annotations
from typing import Dict, Any
from .registry import load_json

def load_capability_spec():
    return load_json("registry/capabilities.json")

def resolve_capabilities(ir: Dict[str, Any], provided: Dict[str, bool] | None = None) -> Dict[str, Any]:
    spec = load_capability_spec()
    available = dict(spec.get("default_runtime", {}))
    if provided:
        available.update({str(k): bool(v) for k, v in provided.items()})

    requirements = {}
    missing_required = set()
    requested_tools = set()
    available_requested = set()
    option_names = set(ir.get("tool_intents", [])) | set(ir.get("options", {}).keys())

    for cmd in ir.get("commands", []):
        req = spec.get("command_requirements", {}).get(cmd, {})
        base = list(req.get("base", []))
        missing = [cap for cap in base if not available.get(cap, False)]
        missing_required.update(missing)

        for opt, cap in req.get("option_requirements", {}).items():
            if opt in option_names:
                requested_tools.add(cap)
                if available.get(cap, False):
                    available_requested.add(cap)
                else:
                    missing_required.add(cap)

        requirements[cmd] = {
            "required": base,
            "optional": list(req.get("optional", [])),
            "missing_required": missing
        }

    return {
        "available": available,
        "requirements": requirements,
        "requested_tool_capabilities": sorted(requested_tools),
        "available_requested_tool_capabilities": sorted(available_requested),
        "missing_required": sorted(missing_required),
        "can_execute_semantically": not missing_required
    }
