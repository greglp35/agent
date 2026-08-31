from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
import hmac,json
from .engine import compile_command, run_production
from .policy_packs import Actor, PolicyEngine, PolicyApprovalGate, load_policy_pack
from .observability import MetricsRegistry, RunObserver
from .baseline import CrossProviderBaseline
from .evals import EvaluationHarness

class AuthenticationError(PermissionError): pass

class StaticTokenAuthenticator:
    def __init__(self, tokens: dict[str,dict[str,Any]]): self.tokens=tokens
    def authenticate(self, headers: dict[str,str]) -> Actor:
        auth=headers.get("authorization") or headers.get("Authorization") or ""
        if not auth.lower().startswith("bearer "): raise AuthenticationError("Bearer token required")
        supplied=auth.split(" ",1)[1]
        for token,spec in self.tokens.items():
            if hmac.compare_digest(token,supplied): return Actor(str(spec["subject"]),tuple(spec.get("roles",[])))
        raise AuthenticationError("Invalid bearer token")

@dataclass
class APIResponse:
    status: int
    body: dict[str,Any] | str
    content_type: str="application/json"

class CommandOSAPI:
    def __init__(self, *, providers: dict[str,Callable[[],Any]], authenticator, tool_adapters=None,
                 metrics: MetricsRegistry | None=None, journal=None, eval_cases=None, policy_root=None):
        self.providers=providers; self.authenticator=authenticator; self.tool_adapters=tool_adapters or {}
        self.metrics=metrics or MetricsRegistry(); self.observer=RunObserver(self.metrics,journal)
        self.journal=journal; self.eval_cases=eval_cases or []; self.policy_root=policy_root

    def _actor(self,headers): return self.authenticator.authenticate(headers)
    def _pack(self,name): return load_policy_pack(name or "default",root=self.policy_root)
    def _require_api(self,actor: Actor,pack, capability: str):
        PolicyEngine(pack).authorize(actor,capability=capability,effect="read")

    def handle(self, method: str, path: str, body: dict[str,Any] | None=None, headers: dict[str,str] | None=None) -> APIResponse:
        body=body or {}; headers=headers or {}; operation=f"{method.upper()} {path}"
        trace,started=self.observer.start(operation)
        status="error"
        try:
            if method.upper()=="GET" and path=="/health":
                status="ok"; return APIResponse(200,{"status":"ok","service":"command-os","version":"2.0.0-beta.1"})
            if method.upper()=="GET" and path=="/metrics":
                status="ok"; return APIResponse(200,self.metrics.render_prometheus(),"text/plain; version=0.0.4")
            actor=self._actor(headers); pack=self._pack(body.get("policy_pack")); engine=PolicyEngine(pack)
            if method.upper()=="POST" and path=="/v1/compile":
                self._require_api(actor,pack,"local.compile"); status="ok"
                return APIResponse(200,compile_command(str(body.get("command") or "")))
            if method.upper()=="POST" and path=="/v1/run":
                self._require_api(actor,pack,"llm.reason")
                provider=str(body.get("provider") or ""); factory=self.providers.get(provider)
                if factory is None: return APIResponse(400,{"error":"unknown_provider","provider":provider})
                approver=None; approver_header=headers.get("x-command-os-approver") or headers.get("X-Command-OS-Approver")
                if approver_header: approver=self.authenticator.authenticate({"authorization":f"Bearer {approver_header}"})
                gate=PolicyApprovalGate(engine,actor,approver)
                result=run_production(str(body.get("command") or ""),factory(),journal=self.journal,
                    tool_adapters=self.tool_adapters,approval_gate=gate,state=body.get("state"),
                    council_parallel=bool(body.get("council_parallel",False)))
                status="ok"; return APIResponse(200,result)
            if method.upper()=="POST" and path=="/v1/evaluate":
                self._require_api(actor,pack,"llm.reason")
                names=body.get("providers") or list(self.providers); factories={n:self.providers[n] for n in names if n in self.providers}
                harness=EvaluationHarness(body.get("cases") or self.eval_cases); result=CrossProviderBaseline(harness).run(factories)
                status="ok"; return APIResponse(200,result)
            return APIResponse(404,{"error":"not_found"})
        except AuthenticationError as exc:
            return APIResponse(401,{"error":"authentication_failed","message":str(exc)})
        except PermissionError as exc:
            return APIResponse(403,{"error":"forbidden","message":str(exc)})
        except Exception as exc:
            return APIResponse(400,{"error":type(exc).__name__,"message":str(exc)})
        finally:
            self.observer.finish(trace,started,operation,status)
