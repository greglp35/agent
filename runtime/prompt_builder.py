from __future__ import annotations
import json
from typing import Any, Dict, Iterable
from .adapters.base import LLMRequest


def _expert_summary(expert: Dict[str, Any]) -> str:
    return "\n".join([
        f"Expert: {expert.get('id', expert.get('domain', 'unknown'))}",
        f"Mission: {expert.get('mission', '')}",
        "Standards: " + ", ".join(expert.get("standards", [])),
        "Questions de contrôle: " + " | ".join(expert.get("questions", [])),
        "Modes d'échec à surveiller: " + ", ".join(expert.get("failure_modes", [])),
    ])


def build_command_request(step: Dict[str, Any], command_spec: Dict[str, Any], *, expert_specs: Iterable[Dict[str, Any]] = (),
                          previous_outputs: list[Dict[str, Any]] | None = None, tool_context: Dict[str, Any] | None = None,
                          available_tools: list[str] | None = None) -> LLMRequest:
    previous_outputs=previous_outputs or []; tool_context=tool_context or {}; available_tools=available_tools or []
    expert_block="\n\n".join(_expert_summary(x) for x in expert_specs)
    profile=step.get("profile") or {}; directives=profile.get("directives",[]) if isinstance(profile,dict) else []
    system="""Tu exécutes une étape de COMMAND OS. Respecte le contrat de sortie et la vérité d'exécution.
Ne prétends jamais avoir utilisé un outil absent. Distingue faits, inférences, hypothèses et inconnues.
Ne révèle pas de raisonnement privé détaillé : fournis uniquement conclusions, preuves, hypothèses, objections pertinentes et justification concise.
Si une action externe est réellement nécessaire, demande-la uniquement via `tool_requests` sous forme d'une liste de {capability, arguments}. Ne prétends pas qu'elle a été exécutée.
"""
    if directives: system += "\nProfil actif — directives:\n- " + "\n- ".join(directives)
    if expert_block: system += "\nExpertises activées:\n" + expert_block
    user_payload={"command":step.get("command"),"mission":command_spec.get("mission"),"target":step.get("target"),
        "depth":step.get("depth"),"methods":step.get("methods",[]),"lenses":step.get("lenses",[]),
        "output_preferences":step.get("output_preferences",{}),"profile":profile,
        "previous_outputs":previous_outputs,"tool_context":tool_context,"available_tools":available_tools}
    contract={"required_outputs":command_spec.get("default_output",[]),"required_meta":["summary","epistemic","confidence"],
              "optional_meta":["tool_requests"],"epistemic_keys":["facts","inferences","assumptions","unknowns"]}
    return LLMRequest(purpose="command_execution",system=system,user=json.dumps(user_payload,ensure_ascii=False,indent=2),
        metadata={"command":step.get("command"),"depth":step.get("depth"),"target":step.get("target"),"profile":profile.get("id") if isinstance(profile,dict) else None},response_contract=contract)


def build_council_view_request(target: str | None, expert: Dict[str, Any], context: Dict[str, Any]) -> LLMRequest:
    system="""Tu es un membre indépendant d'un conseil d'experts COMMAND OS.
Donne ton avis sans chercher le consensus et sans voir les avis des autres experts.
Utilise tes standards professionnels, signale hypothèses et inconnues, et formule les objections qui pourraient changer la décision.
Si le contexte contient un profil actif, respecte ses directives sans sacrifier ton indépendance d'expert.
"""
    return LLMRequest(purpose="council_expert_view",system=system,user=json.dumps({"target":target,"expert":expert,"context":context},ensure_ascii=False,indent=2),
        metadata={"expert_id":expert.get("id"),"target":target},response_contract={"required_meta":["summary","outputs","epistemic","confidence"]})


def build_council_arbitration_request(target: str | None, views: list[Dict[str, Any]], context: Dict[str, Any]) -> LLMRequest:
    system="""Tu es l'arbitre d'un conseil d'experts COMMAND OS.
Préserve les avis indépendants, identifie les désaccords matériels, explique les critères d'arbitrage et produis une synthèse exploitable.
Ne fabrique pas de consensus. Une divergence non résolue doit rester visible. Respecte les directives du profil actif présentes dans le contexte.
"""
    return LLMRequest(purpose="council_arbitration",system=system,user=json.dumps({"target":target,"independent_views":views,"context":context},ensure_ascii=False,indent=2),
        metadata={"target":target},response_contract={"required_meta":["summary","disagreements","outputs","epistemic","confidence"]})
