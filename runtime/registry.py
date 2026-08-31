from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _load_profiles():
    profiles={}
    root_dir=ROOT / "profiles"
    if root_dir.exists():
        for path in sorted(root_dir.glob("*.json")):
            doc=json.loads(path.read_text(encoding="utf-8")); profiles[doc["id"]]=doc
        return profiles
    try:
        from importlib.resources import files
        data_dir=files("runtime").joinpath("data","profiles")
        for item in data_dir.iterdir():
            if item.name.endswith(".json"):
                doc=json.loads(item.read_text(encoding="utf-8")); profiles[doc["id"]]=doc
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return profiles


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
        "profiles": _load_profiles(),
        "routing_principles": experts_doc.get("routing_principles", {})
    }
