from __future__ import annotations
from .capabilities import resolve_capabilities
from .quality import evaluate_quality_gate

def execute_compiled(compiled, provided_capabilities=None, adapters=None, dry_run=True):
    adapters = adapters or {}
    ir = compiled["ir"]
    cap = resolve_capabilities(ir, provided_capabilities)
    results = []

    for step in compiled["plan"].get("steps", []):
        cmd = step.get("command")
        if not cmd:
            results.append({
                "phase":step.get("phase"), "command":None,
                "status":"EXECUTED", "detail":"Expert routing compiled locally."
            })
            continue

        if dry_run:
            results.append({
                "phase":step.get("phase"), "command":cmd,
                "status":"SIMULATED", "detail":"Dry-run: planned, not semantically executed."
            })
            continue

        adapter = adapters.get(cmd)
        if adapter:
            try:
                payload = adapter(step) or {}
                results.append({
                    "phase":step.get("phase"), "command":cmd,
                    "status":payload.get("status","EXECUTED"),
                    "detail":payload
                })
            except Exception as exc:
                results.append({
                    "phase":step.get("phase"), "command":cmd,
                    "status":"BLOCKED", "detail":{"error":str(exc)}
                })
            continue

        missing = cap.get("requirements", {}).get(cmd, {}).get("missing_required", [])
        if missing:
            detail = {"missing_capabilities":missing}
        else:
            detail = {"reason":"No execution adapter registered for this command."}
        results.append({
            "phase":step.get("phase"), "command":cmd,
            "status":"NOT_AVAILABLE", "detail":detail
        })

    quality = evaluate_quality_gate(compiled, results)
    statuses = [r["status"] for r in results if r.get("command")]

    if not statuses:
        overall = "EXECUTED"
    elif all(s=="EXECUTED" for s in statuses):
        overall = "EXECUTED"
    elif any(s=="BLOCKED" for s in statuses):
        overall = "BLOCKED"
    elif all(s=="SIMULATED" for s in statuses):
        overall = "SIMULATED"
    elif all(s=="NOT_AVAILABLE" for s in statuses):
        overall = "NOT_AVAILABLE"
    else:
        overall = "PARTIALLY_EXECUTED"

    return {
        "execution_status":overall,
        "capabilities":cap,
        "steps":results,
        "quality_gate":quality
    }
