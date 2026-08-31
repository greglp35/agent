from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from .policy import ApprovalRequired


@dataclass
class ApprovalGate:
    required_effects: frozenset[str] = frozenset({"write", "external_side_effect", "destructive", "production_deploy"})
    approver: Callable[[str, dict[str, Any]], bool] | None = None

    def require(self, effect: str, context: dict[str, Any]) -> None:
        if effect not in self.required_effects:
            return
        if self.approver is None or not bool(self.approver(effect, context)):
            raise ApprovalRequired(f"Approval required for effect={effect}")
