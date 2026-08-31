from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict
from .adapters.base import LLMAdapter
from .prompt_builder import build_council_view_request, build_council_arbitration_request


class CouncilRunner:
    def __init__(self, llm: LLMAdapter, *, max_experts: int = 5, parallel: bool = False, max_workers: int = 4):
        self.llm = llm
        self.max_experts = max(1, max_experts)
        self.parallel = parallel
        self.max_workers = max(1, max_workers)

    def _experts(self, routing: Dict[str, Any]) -> list[Dict[str, Any]]:
        ordered = list(routing.get("primary", [])) + list(routing.get("secondary", []))
        seen = set()
        result = []
        for expert in ordered:
            eid = expert.get("id")
            if not eid or eid in seen:
                continue
            seen.add(eid)
            result.append(expert)
            if len(result) >= self.max_experts:
                break
        return result

    def _one_view(self, target: str | None, expert: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        request = build_council_view_request(target, expert, context)
        response = self.llm.complete(request)
        return {
            "expert_id": expert.get("id"),
            "domain": expert.get("domain"),
            "response": response.content,
            "model": response.model,
        }

    def run(self, target: str | None, routing: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        experts = self._experts(routing)
        if not experts:
            return {
                "status": "BLOCKED",
                "summary": "No experts were routed for council execution.",
                "independent_views": [],
                "disagreements": [],
            }

        views: list[Dict[str, Any]] = []
        can_parallel = self.parallel and bool(getattr(self.llm, "thread_safe", False)) and len(experts) > 1
        if can_parallel:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(experts))) as pool:
                futures = {pool.submit(self._one_view, target, expert, context): idx for idx, expert in enumerate(experts)}
                ordered: Dict[int, Dict[str, Any]] = {}
                for future in as_completed(futures):
                    ordered[futures[future]] = future.result()
                views = [ordered[i] for i in sorted(ordered)]
        else:
            views = [self._one_view(target, expert, context) for expert in experts]

        arbitration_req = build_council_arbitration_request(target, views, context)
        arbitration = self.llm.complete(arbitration_req)
        content = dict(arbitration.content)
        content.setdefault("independent_views", views)
        content.setdefault("disagreements", [])
        content["status"] = "EXECUTED"
        content["council_meta"] = {
            "experts": [x.get("expert_id") for x in views],
            "parallel": can_parallel,
            "arbiter_model": arbitration.model,
        }
        return content
