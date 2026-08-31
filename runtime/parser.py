from __future__ import annotations
import shlex
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

DEPTH_NAMES = {"fast":"FAST","standard":"STANDARD","deep":"DEEP","forensic":"FORENSIC"}

def _tokenize(raw: str) -> List[str]:
    # shlex keeps quoted multi-word values intact.
    # We force >> to be a standalone token when it is outside ordinary words.
    cooked = raw.replace(">>", " >> ")
    return shlex.split(cooked, posix=True)

def _diag(level: str, code: str, message: str) -> Dict[str, str]:
    return {"level": level, "code": code, "message": message}

def _split_stages(tokens: List[str]) -> List[List[str]]:
    stages, current = [], []
    for tok in tokens:
        if tok == ">>":
            stages.append(current)
            current = []
        else:
            current.append(tok)
    stages.append(current)
    return stages

def _parse_command_token(tok: str):
    body = tok[1:]
    if "=" in body:
        name, arg = body.split("=", 1)
        return name, arg
    return body, None

def _parse_option_token(tok: str):
    body = tok[2:]
    if "=" in body:
        name, value = body.split("=", 1)
        return name, value
    return body, True

def _phase_rank(name: str, command_class: Optional[str] = None) -> int:
    explicit = {
        "expert":10, "council":10,
        "research":20, "verify":20, "benchmark":20, "data":20,
        "deepthink":30, "challenge":30,
        "audit":40, "debug":40, "risk":40, "spec":40, "compare":40,
        "strategy":40, "forecast":40, "architect":40, "simulate":40,
        "experiment":40, "measure":40, "ideate":40, "optimize":40,
        "simplify":40, "redteam":45,
        "prioritize":50, "decision":60, "plan":70,
        "build":80, "automate":80,
        "test":90,
        "write":100, "copywriter":100, "summarize":100, "teach":100,
        "continue":110, "next":110, "deeper":110, "fix":110, "redo":110,
        "focus":110, "final":110,
    }
    return explicit.get(name, 50)

def parse_command_line(raw: str, registries: Dict[str, Any], source: str = "user") -> Dict[str, Any]:
    diagnostics = []

    if source != "user":
        return {
            "version":"2.0",
            "raw":raw,
            "source":source,
            "strict_order":False,
            "macro":None,
            "target":raw.strip() or None,
            "commands":[],
            "normalized_commands":[],
            "depth":"STANDARD",
            "methods":[],
            "lenses":[],
            "tool_intents":[],
            "output_preferences":{},
            "options":{},
            "stages":[],
            "diagnostics":[_diag("INFO","I300 DATA_ONLY_SOURCE","Slash commands embedded in non-user data are not executable.")]
        }

    tokens = _tokenize(raw)
    strict_order = ">>" in tokens
    stage_tokens = _split_stages(tokens)

    all_commands = []
    all_methods = []
    all_lenses = []
    tool_intents = []
    output_preferences = {}
    global_options = {}
    depth_events = []
    parsed_stages = []
    macro_name = None

    commands_reg = registries["commands"]
    methods_reg = registries["methods"]
    modifiers_reg = registries["modifiers"]
    macros_reg = registries["macros"]
    aliases_reg = registries["aliases"]

    for seg in stage_tokens:
        seg_commands = []
        subject_parts = []
        seg_options = {}

        for tok in seg:
            if tok.startswith("/") and len(tok) > 1:
                name, arg = _parse_command_token(tok)

                # Macro
                if name in macros_reg:
                    if macro_name is None:
                        macro_name = name
                    else:
                        diagnostics.append(_diag("WARNING","W207 MULTIPLE_MACROS","Plusieurs macros ont été fournies ; elles seront toutes développées dans l’ordre."))
                    seg_commands.append({"name":name, "arg":arg, "kind":"macro"})
                    continue

                # Alias command
                if name in aliases_reg:
                    alias = aliases_reg[name]
                    exp = alias["expands_to"]
                    if "command" in exp:
                        canonical = exp["command"]
                        seg_commands.append({"name":canonical, "arg":arg, "kind":"command", "via_alias":name})
                        diagnostics.append(_diag("WARNING","W205 ALIAS_EXPANDED",f"/{name} → /{canonical}"))
                        for k,v in exp.get("options", {}).items():
                            seg_options[k] = v
                    elif "option" in exp:
                        seg_options[exp["option"]] = True
                        diagnostics.append(_diag("WARNING","W205 ALIAS_EXPANDED",f"/{name} → --{exp['option']}"))
                    continue

                if name not in commands_reg:
                    diagnostics.append(_diag("ERROR","E101 UNKNOWN_COMMAND",f"Commande inconnue : /{name}"))
                    seg_commands.append({"name":name, "arg":arg, "kind":"unknown"})
                else:
                    seg_commands.append({"name":name, "arg":arg, "kind":"command"})
                continue

            if tok.startswith("--") and len(tok) > 2:
                name, value = _parse_option_token(tok)
                seg_options[name] = value

                if name in DEPTH_NAMES:
                    depth_events.append(name)
                elif name in methods_reg:
                    if name not in all_methods:
                        all_methods.append(name)
                elif name in modifiers_reg:
                    mod = modifiers_reg[name]
                    cat = mod.get("category")
                    if cat == "lens" and name not in all_lenses:
                        all_lenses.append(name)
                    elif cat == "tool_intent" and name not in tool_intents:
                        tool_intents.append(name)
                    elif cat == "output":
                        output_preferences[name] = value
                    elif cat in ("presentation","style","content","audience","posture","routing","evidence"):
                        global_options[name] = value
                else:
                    diagnostics.append(_diag("WARNING","W201 UNKNOWN_OPTION",f"Option ou méthode inconnue : --{name}"))
                continue

            subject_parts.append(tok)

        target = " ".join(subject_parts).strip() or None
        parsed_stages.append({
            "commands":[x["name"] for x in seg_commands],
            "command_nodes":seg_commands,
            "target":target,
            "options":seg_options,
        })

    # Depth resolution
    depth = "STANDARD"
    if depth_events:
        depth = DEPTH_NAMES[depth_events[-1]]
        if len(depth_events) > 1:
            diagnostics.append(_diag("WARNING","W202 CONFLICTING_DEPTH",f"Profondeurs multiples {depth_events}; la dernière gagne : {depth}."))

    # Gather command list before macro expansion
    for st in parsed_stages:
        for n in st["commands"]:
            all_commands.append(n)

    # Macro expansion into stages, preserving macro target/options.
    expanded_stages = []
    expanded_any = False
    for st in parsed_stages:
        new_commands = []
        for node in st["command_nodes"]:
            if node["kind"] != "macro":
                new_commands.append(node["name"])
                continue
            expanded_any = True
            macro = macros_reg[node["name"]]
            for item in macro["pipeline"]:
                cmd = item if isinstance(item, str) else item["command"]
                new_commands.append(cmd)
            for m in macro.get("default_methods", []):
                if m not in all_methods:
                    all_methods.append(m)
            for opt in macro.get("default_modifiers", []):
                if opt in methods_reg and opt not in all_methods:
                    all_methods.append(opt)
                elif opt in modifiers_reg:
                    cat = modifiers_reg[opt].get("category")
                    if cat == "lens" and opt not in all_lenses:
                        all_lenses.append(opt)
                    elif cat == "output":
                        output_preferences[opt] = True
                    else:
                        global_options[opt] = True
            if not depth_events and macro.get("default_depth"):
                depth = macro["default_depth"]
            diagnostics.append(_diag("WARNING","W206 MACRO_EXPANDED",f"/{node['name']} développé en pipeline canonique."))
        expanded_stages.append({
            "commands":new_commands,
            "target":st["target"],
            "options":st["options"]
        })

    if expanded_any:
        parsed_stages = expanded_stages
        all_commands = [c for st in parsed_stages for c in st["commands"]]

    # Apply options discovered inside stage parsing to global semantics.
    for st in parsed_stages:
        for name, value in st.get("options", {}).items():
            if name in DEPTH_NAMES:
                # already accounted in initial pass
                continue
            if name in methods_reg and name not in all_methods:
                all_methods.append(name)
            elif name in modifiers_reg:
                mod = modifiers_reg[name]
                cat = mod.get("category")
                if cat == "lens" and name not in all_lenses:
                    all_lenses.append(name)
                elif cat == "tool_intent" and name not in tool_intents:
                    tool_intents.append(name)
                elif cat == "output":
                    output_preferences[name] = value
                else:
                    global_options[name] = value

    # Normalize non-strict command order per stage.
    normalized_commands = []
    for st in parsed_stages:
        original = list(st["commands"])
        normalized = sorted(
            original,
            key=lambda n: _phase_rank(n, commands_reg.get(n, {}).get("class"))
        )
        st["normalized_commands"] = normalized
        normalized_commands.extend(normalized)
        if normalized != original and not strict_order:
            diagnostics.append(_diag("INFO","I301 PIPELINE_NORMALIZED",f"Segment normalisé : {original} → {normalized}"))
        if strict_order:
            # Within each strict segment we allow local normalization, but stage order is immutable.
            pass

    # Resolve overall target as first non-empty stage target.
    overall_target = next((st["target"] for st in parsed_stages if st.get("target")), None)

    # Basic required-context diagnostics.
    if "compare" in all_commands:
        compare_stage = next((st for st in parsed_stages if "compare" in st["commands"]), None)
        comp_target = compare_stage.get("target") if compare_stage else None
        if not comp_target:
            diagnostics.append(_diag("WARNING","W203 CONTEXT_REQUIRED","/compare nécessite des alternatives ou un contexte conversationnel permettant de les résoudre."))
    for cmd in all_commands:
        reg = commands_reg.get(cmd)
        if reg and reg.get("requires_target") and overall_target is None:
            diagnostics.append(_diag("WARNING","W203 CONTEXT_REQUIRED",f"/{cmd} nécessite une cible ou un contexte résolvable."))
            break

    return {
        "version":"2.0",
        "raw":raw,
        "source":source,
        "strict_order":strict_order,
        "macro":macro_name,
        "target":overall_target,
        "commands":all_commands,
        "normalized_commands":normalized_commands,
        "depth":depth,
        "methods":all_methods,
        "lenses":all_lenses,
        "tool_intents":tool_intents,
        "output_preferences":output_preferences,
        "options":global_options,
        "stages":parsed_stages,
        "diagnostics":diagnostics,
    }
