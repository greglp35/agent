from __future__ import annotations
from typing import Any, Dict
from .adapters.base import LLMAdapter
from .capabilities import resolve_capabilities
from .continuity import resolve_continuity
from .council import CouncilRunner
from .prompt_builder import build_command_request
from .registry import load_registries
from .semantic_quality import evaluate_semantic_quality
from .tool_router import ToolRouter


class SemanticRuntime:
    def __init__(self, llm: LLMAdapter, *, tool_adapters: Dict[str, Any] | None = None,
                 council_parallel: bool = False, council_max_experts: int = 5):
        self.llm=llm
        self.registries=load_registries()
        self.tool_router=ToolRouter(tool_adapters)
        self.council=CouncilRunner(llm,max_experts=council_max_experts,parallel=council_parallel)

    def _selected_expert_specs(self, compiled):
        routing=compiled.get("ir",{}).get("routing",{})
        ids=[]
        for group in ("primary","secondary","review"):
            for item in routing.get(group,[]):
                eid=item.get("id")
                if eid and eid not in ids: ids.append(eid)
        return [self.registries["experts"][eid] for eid in ids if eid in self.registries["experts"]]

    def execute(self, compiled, *, state=None, provided_capabilities=None):
        capabilities=dict(provided_capabilities or {})
        capabilities["llm.reason"]=True
        for capability in self.tool_router.adapters: capabilities[capability]=True
        cap=resolve_capabilities(compiled["ir"],capabilities)
        results=[]; previous_outputs=[]; expert_specs=self._selected_expert_specs(compiled)

        for raw_step in compiled.get("plan",{}).get("steps",[]):
            if not raw_step.get("command"):
                results.append({"phase":raw_step.get("phase"),"command":None,"status":"EXECUTED",
                                "content":{"routing":raw_step.get("details",{})}})
                continue
            step=resolve_continuity(raw_step,state); command=step.get("command")
            if command=="council":
                try:
                    content=self.council.run(step.get("target"),compiled["ir"].get("routing",{}),
                        context={"previous_outputs":previous_outputs,"depth":step.get("depth")})
                    status=content.pop("status","EXECUTED")
                except Exception as exc:
                    content={"error":str(exc)}; status="BLOCKED"
                result={"phase":step.get("phase"),"command":command,"status":status,"content":content}
                results.append(result)
                if status=="EXECUTED": previous_outputs.append({"command":command,"content":content})
                continue
            if not step.get("target") and command in {"continue","next","deeper","fix","redo","focus","final"}:
                results.append({"phase":step.get("phase"),"command":command,"status":"BLOCKED",
                                "content":{"error":"No active work state could resolve the continuity target."}})
                continue
            try:
                tool_context=self.tool_router.acquire(compiled["ir"],step)
                command_spec=self.registries["commands"].get(command,{"name":command,"mission":"","default_output":[]})
                request=build_command_request(step,command_spec,expert_specs=expert_specs,
                    previous_outputs=previous_outputs,tool_context=tool_context,
                    available_tools=self.tool_router.available())
                response=self.llm.complete(request); content=response.content
                tool_results=self.tool_router.execute_requests(content.get("tool_requests") if isinstance(content,dict) else None,step=step)
                if tool_results and isinstance(content,dict): content={**content,"tool_results":tool_results}
                blocked_tool=any(x.get("status")=="BLOCKED" for x in tool_results)
                result={"phase":step.get("phase"),"command":command,
                        "status":"PARTIALLY_EXECUTED" if blocked_tool else "EXECUTED",
                        "content":content,"model":response.model,"usage":response.usage,
                        "tool_context_used":sorted(tool_context.keys()),"tool_results":tool_results}
                results.append(result)
                previous_outputs.append({"command":command,"content":content})
            except Exception as exc:
                results.append({"phase":step.get("phase"),"command":command,"status":"BLOCKED","content":{"error":str(exc)}})

        statuses=[x["status"] for x in results if x.get("command")]
        if statuses and all(x=="EXECUTED" for x in statuses): overall="EXECUTED"
        elif any(x=="BLOCKED" for x in statuses): overall="PARTIALLY_EXECUTED" if any(x in {"EXECUTED","PARTIALLY_EXECUTED"} for x in statuses) else "BLOCKED"
        elif any(x=="PARTIALLY_EXECUTED" for x in statuses): overall="PARTIALLY_EXECUTED"
        elif statuses: overall="PARTIALLY_EXECUTED"
        else: overall="EXECUTED"
        quality=evaluate_semantic_quality(compiled,results)
        return {"execution_status":overall,"host":getattr(self.llm,"name",type(self.llm).__name__),
                "capabilities":cap,"steps":results,"quality_gate":quality,
                "final_output":previous_outputs[-1] if previous_outputs else None,
                "budget":getattr(getattr(self.llm,"budget",None),"snapshot",lambda:None)()}
