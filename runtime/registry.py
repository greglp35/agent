from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

def load_registries():
    commands_doc = load_json("registry/commands.json")
    methods_doc = load_json("registry/methods.json")
    modifiers_doc = load_json("registry/modifiers.json")
    macros_doc = load_json("registry/macros.json")
    aliases_doc = load_json("registry/aliases.json")
    experts_doc = load_json("experts/expert-registry.json")

    return {
        "commands": {x["name"]: x for x in commands_doc["commands"]},
        "methods": {x["name"]: x for x in methods_doc["methods"]},
        "modifiers": {x["name"]: x for x in modifiers_doc["modifiers"]},
        "macros": {x["name"]: x for x in macros_doc["macros"]},
        "aliases": {x["alias"]: x for x in aliases_doc["aliases"]},
        "experts": {x["id"]: x for x in experts_doc["experts"]},
        "routing_principles": experts_doc.get("routing_principles", {})
    }
