from __future__ import annotations
from typing import Dict, Any, List

def _stage_type(command: str) -> str:
    if command in {"expert","council"}: return "ROLE"
    if command in {"research","verify","benchmark","data"}: return "ACQUIRE"
    if command in {"deepthink","challenge"}: return "REASON"
    if command in {"decision"}: return "DECIDE"
    if command in {"prioritize"}: return "PRIORITIZE"
    if command in {"plan"}: return "PLAN"
    if command in {"build","automate"}: return "EXECUTE"
    if command in {"test"}: return "TEST"
    if command in {"write","copywriter","summarize","teach"}: return "PRESENT"
    if command in {"continue","next","deeper","fix","redo","focus","final"}: return "CONTINUITY"
    return "OPERATE"

def build_execution_plan(ir: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
    steps: List[Dict[str, Any]] = []
    if routing.get("primary") or routing.get("secondary") or routing.get("review"):
        steps.append({
            "phase":"ROLE",
            "action":"route_experts",
            "details":routing
        })

    for idx, stage in enumerate(ir.get("stages", []), start=1):
        commands = stage.get("commands", [])
        ordered = commands if ir.get("strict_order") else stage.get("normalized_commands", commands)
        for cmd in ordered:
            steps.append({
                "phase":_stage_type(cmd),
                "command":cmd,
                "target":stage.get("target") or ir.get("target"),
                "depth":ir.get("depth"),
                "methods":ir.get("methods", []),
                "lenses":ir.get("lenses", []),
            })

    quality_checks = []
    command_set = set(ir.get("commands", []))
    if command_set.intersection({"audit","verify","research","decision","build","debug","test","risk"}):
        quality_checks.append("truthfulness_and_evidence")
    if command_set.intersection({"build","automate","debug"}):
        quality_checks.append("execution_status")
        quality_checks.append("regression_or_validation")
    if "council" in command_set:
        quality_checks.append("independent_views_before_synthesis")
        quality_checks.append("surface_material_disagreements")
    if ir.get("depth") == "FORENSIC":
        quality_checks += [
            "root_causes",
            "contradictions",
            "failure_scenarios",
            "missing_evidence",
            "confidence"
        ]

    return {
        "version":"2.0",
        "strict_order":ir.get("strict_order", False),
        "target":ir.get("target"),
        "steps":steps,
        "quality_gate":{
            "required_checks":list(dict.fromkeys(quality_checks)),
            "priority_scale":["P0","P1","P2","P3"],
            "execution_status_required":bool(command_set.intersection({"build","automate","debug"}))
        }
    }
