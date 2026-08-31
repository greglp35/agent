from __future__ import annotations
from pathlib import Path
from typing import Any, Callable
import json, os
from .adapters import OpenAIResponsesAdapter, AnthropicMessagesAdapter

class ProviderRegistry:
    def __init__(self, data: dict[str,Any]): self.data=data; self.providers=data.get("providers",{})
    @classmethod
    def from_default(cls):
        p=Path(__file__).resolve().parents[1]/"registry"/"providers.json"
        if p.exists(): return cls(json.loads(p.read_text(encoding="utf-8")))
        from importlib.resources import files
        resource=files("runtime").joinpath("data","registry","providers.json")
        return cls(json.loads(resource.read_text(encoding="utf-8")))
    def names(self): return sorted(self.providers)
    def build(self, name: str, *, env: dict[str,str] | None=None, transport=None):
        env=env or os.environ; spec=self.providers.get(name)
        if spec is None: raise KeyError(f"Unknown provider: {name}")
        model=env.get(spec.get("model_env",""))
        if not model: raise ValueError(f"Model must be configured via {spec.get('model_env')}")
        api_key=env.get(spec.get("api_key_env",""))
        endpoint=env.get(spec.get("endpoint_env","")) or None
        kind=spec.get("adapter")
        kwargs={"api_key":api_key,"transport":transport}
        if endpoint: kwargs["endpoint"]=endpoint
        if kind=="openai_responses": return OpenAIResponsesAdapter(model,**kwargs)
        if kind=="anthropic_messages": return AnthropicMessagesAdapter(model,**kwargs)
        raise ValueError(f"Unsupported provider adapter: {kind}")
