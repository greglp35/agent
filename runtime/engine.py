from __future__ import annotations
from .registry import load_registries
from .parser import parse_command_line
from .router import route_experts
from .planner import build_execution_plan
from .executor import execute_compiled

def compile_command(raw: str, source: str = "user"):
    registries = load_registries()
    ir = parse_command_line(raw, registries, source=source)
    routing = route_experts(ir, registries)
    ir["routing"] = routing
    plan = build_execution_plan(ir, routing)
    return {"ir":ir, "plan":plan}

def run_command(raw: str, source: str = "user", provided_capabilities=None, adapters=None, dry_run: bool = True):
    compiled = compile_command(raw, source=source)
    execution = execute_compiled(
        compiled,
        provided_capabilities=provided_capabilities,
        adapters=adapters,
        dry_run=dry_run
    )
    return {**compiled, "execution":execution}
