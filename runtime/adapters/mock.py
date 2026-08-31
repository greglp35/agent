from __future__ import annotations

from typing import Any, Dict
from .base import LLMRequest, LLMResponse


class DeterministicLLMAdapter:
    """Predictable adapter used by examples and tests; it performs no network call."""

    name = "deterministic-test-host"
    thread_safe = True

    def __init__(self):
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        meta = request.metadata
        command = meta.get("command") or request.purpose
        expert_id = meta.get("expert_id")

        if request.purpose == "council_expert_view":
            content = {
                "summary": f"Independent view from {expert_id}",
                "outputs": {"recommendation": f"Review target as {expert_id}"},
                "epistemic": {
                    "facts": [],
                    "inferences": [f"Synthetic inference from {expert_id}"],
                    "assumptions": ["Deterministic test adapter"],
                    "unknowns": []
                },
                "confidence": {"level": "medium", "reason": "Deterministic test response"}
            }
        elif request.purpose == "council_arbitration":
            content = {
                "summary": "Council synthesis",
                "independent_views_preserved": True,
                "disagreements": ["Synthetic disagreement for test coverage"],
                "outputs": {"synthesis": "Arbitrated council result"},
                "epistemic": {
                    "facts": [],
                    "inferences": ["Council arbitration generated from independent views"],
                    "assumptions": [],
                    "unknowns": []
                },
                "confidence": {"level": "medium", "reason": "Deterministic arbitration"}
            }
        else:
            fields = list(request.response_contract.get("required_outputs", []))
            outputs: Dict[str, Any] = {field: f"synthetic:{field}" for field in fields}
            if meta.get("depth") == "FORENSIC":
                outputs.setdefault("root_causes", ["synthetic root cause"])
                outputs.setdefault("failure_scenarios", ["synthetic failure scenario"])
            content = {
                "summary": f"Synthetic semantic result for /{command}",
                "outputs": outputs,
                "epistemic": {
                    "facts": [],
                    "inferences": [f"Synthetic inference for {command}"],
                    "assumptions": ["Deterministic test adapter"],
                    "unknowns": []
                },
                "confidence": {"level": "medium", "reason": "Deterministic test response"}
            }

        return LLMResponse(content=content, model=self.name)
