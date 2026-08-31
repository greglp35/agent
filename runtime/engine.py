from __future__ import annotations
from .registry import load_registries
from .parser import parse_command_line
from .profiles import expand_profile_shortcuts, apply_profile
from .router import route_experts
from .planner import build_execution_plan
from .executor import execute_compiled


def compile_command(raw: str, source: str = "user"):
    registries=load_registries()
    expanded=expand_profile_shortcuts(raw,registries.get("profiles",{})) if source=="user" else raw
    ir=parse_command_line(expanded,registries,source=source)
    ir["raw_input"]=raw
    if expanded!=raw: ir["expanded_input"]=expanded
    apply_profile(ir,registries,original_raw=raw)
    routing=route_experts(ir,registries); ir["routing"]=routing
    return {"ir":ir,"plan":build_execution_plan(ir,routing)}


def run_command(raw: str, source: str = "user", provided_capabilities=None, adapters=None, dry_run: bool = True):
    compiled=compile_command(raw,source=source)
    return {**compiled,"execution":execute_compiled(compiled,provided_capabilities=provided_capabilities,adapters=adapters,dry_run=dry_run)}


def run_semantic(raw: str, llm_adapter, *, source: str = "user", tool_adapters=None, state=None,
                 provided_capabilities=None, council_parallel: bool = False, council_max_experts: int = 5):
    from .semantic import SemanticRuntime
    compiled=compile_command(raw,source=source)
    semantic=SemanticRuntime(llm_adapter,tool_adapters=tool_adapters,council_parallel=council_parallel,council_max_experts=council_max_experts)
    execution=semantic.execute(compiled,state=state,provided_capabilities=provided_capabilities)
    return {**compiled,"execution":execution}


def run_production(raw: str, llm_adapter, *, production_policy=None, journal=None, tool_adapters=None,
                   approval_gate=None, source: str = "user", state=None, provided_capabilities=None,
                   council_parallel: bool = False, council_max_experts: int = 5):
    from .adapters import ResilientLLMAdapter, GuardedToolAdapter
    resilient=ResilientLLMAdapter(llm_adapter,policy=production_policy,journal=journal)
    guarded={}
    for capability, adapter in (tool_adapters or {}).items():
        guarded[capability]=GuardedToolAdapter(adapter,approval_gate=approval_gate,journal=journal)
    return run_semantic(raw,resilient,source=source,tool_adapters=guarded,state=state,
        provided_capabilities=provided_capabilities,council_parallel=council_parallel,
        council_max_experts=council_max_experts)
