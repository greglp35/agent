from __future__ import annotations
import re
from typing import Any, Dict

_DEPTH_RANK={"FAST":0,"STANDARD":1,"DEEP":2,"FORENSIC":3}
_EXPLICIT_DEPTH=re.compile(r"(?:^|\s)--(?:fast|standard|deep|forensic)(?:\s|$)")


def expand_profile_shortcuts(raw: str, profiles: Dict[str, Any]) -> str:
    """Convertit un token `/nomprofil` en `--profile=nomprofil` sans toucher aux autres slash commands."""
    if not profiles or not raw:
        return raw
    pattern=re.compile(r"(?<!\S)/([a-z][a-z0-9_-]*)(?=\s|$)")
    return pattern.sub(lambda m: f"--profile={m.group(1)}" if m.group(1) in profiles else m.group(0), raw)


def _merge_unique(target: list[str], values) -> None:
    for value in values or []:
        if value not in target:
            target.append(value)


def apply_profile(ir: Dict[str, Any], registries: Dict[str, Any], *, original_raw: str | None=None) -> Dict[str, Any]:
    profiles=registries.get("profiles",{})
    name=ir.get("options",{}).get("profile")
    if not name:
        return ir
    profile=profiles.get(str(name))
    if profile is None:
        ir.setdefault("diagnostics",[]).append({"level":"WARNING","code":"W209 UNKNOWN_PROFILE","message":f"Profil inconnu : {name}"})
        return ir

    explicit_depth=bool(_EXPLICIT_DEPTH.search(original_raw or ir.get("raw", "")))
    defaults=profile.get("defaults",{})
    methods=list(ir.get("methods",[])); lenses=list(ir.get("lenses",[]))
    _merge_unique(methods,defaults.get("methods")); _merge_unique(lenses,defaults.get("lenses"))
    output=dict(defaults.get("output_preferences",{})); output.update(ir.get("output_preferences",{}))

    requested_depth=defaults.get("depth",ir.get("depth","STANDARD"))
    rule_depths=[]
    for command in ir.get("commands",[]):
        rule=profile.get("command_rules",{}).get(command,{})
        _merge_unique(methods,rule.get("methods")); _merge_unique(lenses,rule.get("lenses"))
        output.update(rule.get("output_preferences",{}))
        if rule.get("depth"):
            rule_depths.append(rule["depth"])

    if not explicit_depth:
        depths=[requested_depth,*rule_depths]
        ir["depth"]=max(depths,key=lambda x:_DEPTH_RANK.get(x,1)) if depths else ir.get("depth","STANDARD")

    ir["methods"]=methods; ir["lenses"]=lenses; ir["output_preferences"]=output
    ir["profile"]={
        "id":profile["id"],
        "label":profile.get("label",profile["id"]),
        "version":profile.get("version"),
        "directives":list(profile.get("directives",[]))
    }
    ir.setdefault("options",{})["profile"]=profile["id"]
    ir.setdefault("diagnostics",[]).append({"level":"INFO","code":"I303 PROFILE_APPLIED","message":f"Profil /{profile['id']} appliqué."})
    return ir
