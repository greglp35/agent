from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import fnmatch, json
from .production import ApprovalRequired

@dataclass(frozen=True)
class Actor:
    subject: str
    roles: tuple[str, ...]

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    approval_required: bool = False
    reason: str = ""

class PolicyPack:
    def __init__(self, data: dict[str, Any]):
        self.data=data
        self.id=str(data.get("id") or "unnamed")
        self.roles=data.get("roles",{})
        self.approval_required_effects=set(data.get("approval_required_effects",[]))
        self.separation_of_duties_effects=set(data.get("separation_of_duties_effects",[]))

    @classmethod
    def from_json(cls, path: str | Path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _expand_role(self, role: str, seen=None) -> dict[str,set[str]]:
        seen=set(seen or ())
        if role in seen: raise ValueError(f"Role inheritance cycle: {role}")
        seen.add(role)
        spec=self.roles.get(role)
        if spec is None: return {"capabilities":set(),"effects":set(),"can_approve":set()}
        out={"capabilities":set(spec.get("capabilities",[])),"effects":set(spec.get("effects",[])),"can_approve":set(spec.get("can_approve",[]))}
        for parent in spec.get("inherits",[]):
            inherited=self._expand_role(parent,seen)
            for k in out: out[k].update(inherited[k])
        return out

    def permissions_for(self, actor: Actor) -> dict[str,set[str]]:
        out={"capabilities":set(),"effects":set(),"can_approve":set()}
        for role in actor.roles:
            perms=self._expand_role(role)
            for k in out: out[k].update(perms[k])
        return out

def _matches(patterns: Iterable[str], value: str) -> bool:
    return any(p == "*" or fnmatch.fnmatchcase(value,p) for p in patterns)

class PolicyEngine:
    def __init__(self, pack: PolicyPack): self.pack=pack

    def decide(self, actor: Actor, *, capability: str, effect: str) -> PolicyDecision:
        perms=self.pack.permissions_for(actor)
        if not _matches(perms["capabilities"],capability):
            return PolicyDecision(False,False,f"capability denied: {capability}")
        if not _matches(perms["effects"],effect):
            return PolicyDecision(False,False,f"effect denied: {effect}")
        return PolicyDecision(True,effect in self.pack.approval_required_effects,"allowed")

    def can_approve(self, actor: Actor, effect: str) -> bool:
        return _matches(self.pack.permissions_for(actor)["can_approve"],effect)

    def authorize(self, actor: Actor, *, capability: str, effect: str, approver: Actor | None = None) -> PolicyDecision:
        decision=self.decide(actor,capability=capability,effect=effect)
        if not decision.allowed: raise PermissionError(decision.reason)
        if not decision.approval_required: return decision
        if approver is None or not self.can_approve(approver,effect):
            raise ApprovalRequired(f"Approval required for effect={effect}")
        if effect in self.pack.separation_of_duties_effects and approver.subject == actor.subject:
            raise ApprovalRequired(f"Independent approval required for effect={effect}")
        return PolicyDecision(True,True,f"approved by {approver.subject}")

class PolicyApprovalGate:
    def __init__(self, engine: PolicyEngine, actor: Actor, approver: Actor | None = None):
        self.engine=engine; self.actor=actor; self.approver=approver
    def require(self, effect: str, context: dict[str,Any]) -> None:
        capability=str(context.get("capability") or "unknown")
        self.engine.authorize(self.actor,capability=capability,effect=effect,approver=self.approver)

def load_policy_pack(name: str="default", *, root: str | Path | None=None) -> PolicyPack:
    safe=name.replace("/","").replace("\\","")
    if root is not None:
        path=Path(root)/f"{safe}.json"
        if not path.exists(): raise FileNotFoundError(f"Unknown policy pack: {name}")
        return PolicyPack.from_json(path)
    repo_path=Path(__file__).resolve().parents[1]/"policies"/f"{safe}.json"
    if repo_path.exists(): return PolicyPack.from_json(repo_path)
    from importlib.resources import files
    resource=files("runtime").joinpath("data","policies",f"{safe}.json")
    if not resource.is_file(): raise FileNotFoundError(f"Unknown policy pack: {name}")
    return PolicyPack(json.loads(resource.read_text(encoding="utf-8")))
