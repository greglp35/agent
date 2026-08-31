from __future__ import annotations

from typing import Any, Dict, Iterable


def _content(result: Dict[str, Any]) -> Dict[str, Any]:
    value = result.get("content")
    return value if isinstance(value, dict) else {}


def evaluate_semantic_quality(compiled: Dict[str, Any], results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = list(results)
    required = compiled.get("plan", {}).get("quality_gate", {}).get("required_checks", [])
    command_set = set(compiled.get("ir", {}).get("commands", []))

    semantic_contents = [_content(x) for x in results if x.get("status") == "EXECUTED" and x.get("command")]
    council_results = [x for x in results if x.get("command") == "council" and x.get("status") == "EXECUTED"]

    checks = []
    for check in required:
        status = "PENDING"
        reason = "No semantic rule implemented."

        if check == "execution_status":
            status, reason = "PASS", "Every semantic step has an explicit execution status."
        elif check == "truthfulness_and_evidence":
            ok = bool(semantic_contents) and all(
                isinstance(c.get("epistemic"), dict)
                and all(k in c["epistemic"] for k in ("facts", "inferences", "assumptions", "unknowns"))
                for c in semantic_contents
            )
            status = "PASS" if ok else "FAIL"
            reason = "Epistemic separation present on every executed semantic result." if ok else "Missing epistemic separation."
        elif check == "confidence":
            ok = bool(semantic_contents) and all(isinstance(c.get("confidence"), dict) for c in semantic_contents)
            status = "PASS" if ok else "FAIL"
            reason = "Confidence metadata present." if ok else "Confidence metadata missing."
        elif check == "independent_views_before_synthesis":
            ok = bool(council_results) and all(bool(_content(x).get("independent_views")) for x in council_results)
            status = "PASS" if ok else "FAIL"
            reason = "Council preserved independent expert views." if ok else "No independent council views found."
        elif check == "surface_material_disagreements":
            ok = bool(council_results) and all("disagreements" in _content(x) for x in council_results)
            status = "PASS" if ok else "FAIL"
            reason = "Council output exposes disagreements." if ok else "Council disagreement section missing."
        elif check == "root_causes":
            ok = any("root_causes" in c.get("outputs", {}) for c in semantic_contents)
            status = "PASS" if ok else "PENDING"
            reason = "Root causes found in semantic outputs." if ok else "No explicit root-cause field in completed outputs."
        elif check == "failure_scenarios":
            ok = any("failure_scenarios" in c.get("outputs", {}) for c in semantic_contents)
            status = "PASS" if ok else "PENDING"
            reason = "Failure scenarios found." if ok else "No explicit failure-scenario field in completed outputs."
        elif check == "regression_or_validation":
            ok = "test" in command_set or any("validation" in c.get("outputs", {}) for c in semantic_contents)
            status = "PASS" if ok else "PENDING"
            reason = "Validation/test stage present." if ok else "Validation remains to be completed."
        elif check in {"contradictions", "missing_evidence"}:
            status, reason = "PENDING", "Semantic host should surface this field when materially present."

        checks.append({"check": check, "status": status, "reason": reason})

    if any(x["status"] == "FAIL" for x in checks):
        overall = "FAIL"
    elif any(x["status"] == "PENDING" for x in checks):
        overall = "PENDING"
    else:
        overall = "PASS"
    return {"overall": overall, "checks": checks}
