from __future__ import annotations
from typing import Dict, Any, List, Tuple
import unicodedata

def _norm(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s

def route_experts(ir: Dict[str, Any], registries: Dict[str, Any]) -> Dict[str, Any]:
    experts = registries["experts"]
    principles = registries.get("routing_principles", {})
    max_primary = int(principles.get("max_primary_default", 3))
    max_secondary = int(principles.get("max_secondary_default", 4))

    text_parts = [
        ir.get("target") or "",
        " ".join(ir.get("commands", [])),
        " ".join(ir.get("lenses", [])),
        " ".join(ir.get("methods", [])),
    ]
    haystack = _norm(" ".join(text_parts))

    scores: List[Tuple[str, float, List[str]]] = []
    for eid, expert in experts.items():
        score = 0.0
        reasons = []
        for kw in expert.get("keywords", []):
            nkw = _norm(str(kw))
            if nkw and nkw in haystack:
                score += 2.0
                reasons.append(f"keyword:{kw}")
        domain = _norm(expert.get("domain",""))
        if domain and domain in [_norm(x) for x in ir.get("lenses", [])]:
            score += 4.0
            reasons.append(f"lens:{expert.get('domain')}")
        scores.append((eid, score, reasons))

    scores.sort(key=lambda x: (-x[1], x[0]))
    positive = [x for x in scores if x[1] > 0]

    primary = positive[:max_primary]
    secondary = positive[max_primary:max_primary+max_secondary]

    # Reviewers are risk-driven, not automatically primary.
    reviewers = []
    command_set = set(ir.get("commands", []))
    lens_set = set(ir.get("lenses", []))
    if "security" in lens_set and "cybersecurity" not in [x[0] for x in primary+secondary]:
        reviewers.append(("cybersecurity", ["lens:security"]))
    if command_set.intersection({"build","debug","test","audit"}) and "qa_testing" not in [x[0] for x in primary+secondary]:
        reviewers.append(("qa_testing", ["quality-gate"]))
    if command_set.intersection({"decision","compare","prioritize"}) and "decision_science" not in [x[0] for x in primary+secondary]:
        reviewers.append(("decision_science", ["decision-quality"]))

    # If /expert or /council is present and no keyword matched, use generic decision/research experts sparingly.
    if not primary and command_set.intersection({"expert","council"}):
        fallback = "research_analysis" if command_set.intersection({"research","verify","benchmark"}) else "decision_science"
        primary = [(fallback, 1.0, ["fallback:general-expertise"])]

    def render(items):
        out = []
        for item in items:
            eid = item[0]
            reasons = item[2] if len(item) > 2 else item[1]
            out.append({
                "id": eid,
                "domain": experts[eid].get("domain"),
                "mission": experts[eid].get("mission"),
                "reasons": reasons
            })
        return out

    routing = {
        "mode": "council" if "council" in command_set else ("expert" if "expert" in command_set else "implicit"),
        "primary": render(primary),
        "secondary": render(secondary),
        "review": [
            {
                "id": eid,
                "domain": experts[eid].get("domain"),
                "mission": experts[eid].get("mission"),
                "reasons": reasons
            } for eid, reasons in reviewers
        ]
    }
    return routing
